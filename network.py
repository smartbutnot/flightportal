"""
Network and HTTP communication for FlightPortal.
Handles WiFi connections and HTTP requests to Flightradar24 API.
"""

import time
import board
import busio
from digitalio import DigitalInOut
import neopixel
from adafruit_esp32spi import adafruit_esp32spi
from adafruit_esp32spi import adafruit_esp32spi_wifimanager
from adafruit_portalbase.network import HttpError
import adafruit_requests as requests
from microcontroller import watchdog as w

from config import Config
from utils import log_error, log_info, log_warning, debug_print

import secrets as secrets_module


class WiFiManager:
    """Manage WiFi connections and provide robust connectivity."""
    
    def __init__(self):
        """Initialize WiFi hardware and manager."""
        self.esp32_cs = DigitalInOut(board.ESP_CS)
        self.esp32_ready = DigitalInOut(board.ESP_BUSY)
        self.esp32_reset = DigitalInOut(board.ESP_RESET)
        
        self.spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
        self.esp = adafruit_esp32spi.ESP_SPIcontrol(
            self.spi, self.esp32_cs, self.esp32_ready, self.esp32_reset
        )
        
        self.status_light = neopixel.NeoPixel(
            board.NEOPIXEL, 1, brightness=0.2
        )
        
        self.wifi = adafruit_esp32spi_wifimanager.ESPSPI_WiFiManager(
            self.esp, secrets_module.secrets, self.status_light, debug=False, attempts=1
        )
        
        self.is_connected = False
        log_info("WiFi hardware initialized")
    
    def connect(self):
        """Attempt to establish WiFi connection."""
        if self.is_connected and self.esp.status == adafruit_esp32spi.WL_CONNECTED:
            debug_print("Already connected to WiFi")
            return True
        
        log_info("Connecting to WiFi...")
        try:
            self.wifi.connect()
            if self.esp.status == adafruit_esp32spi.WL_CONNECTED:
                self.is_connected = True
                log_info("WiFi connected successfully")
                self.status_light.fill(0x00FF00)  # Green
                return True
            else:
                self.is_connected = False
                log_error("WiFi connection failed")
                self.status_light.fill(0xFF0000)  # Red
                return False
        except Exception as e:
            log_error("WiFi connection error", e)
            self.is_connected = False
            self.status_light.fill(0xFF0000)  # Red
            return False
    
    def disconnect(self):
        """Disconnect from WiFi."""
        try:
            self.wifi.disconnect()
            self.is_connected = False
            log_info("WiFi disconnected")
            return True
        except Exception as e:
            log_error("Error disconnecting from WiFi", e)
            return False
    
    def reconnect(self, max_attempts=None):
        """Attempt to reconnect with optional maximum attempts."""
        if max_attempts is None:
            max_attempts = Config.WiFi_MAX_ATTEMPTS
        
        log_warning(f"Attempting to reconnect WiFi (max {max_attempts} attempts)")
        
        for attempt in range(1, max_attempts + 1):
            log_info(f"Connection attempt {attempt} of {max_attempts}")
            w.feed()
            self.disconnect()
            w.feed()
            
            if self.connect():
                return True
            
            time.sleep(2)
        
        log_error("Failed to reconnect after maximum attempts")
        self.status_light.fill(0xFF0000)  # Red
        return False
    
    def is_online(self):
        """Check if currently connected to WiFi."""
        return self.esp.status == adafruit_esp32spi.WL_CONNECTED


class HTTPClient:
    """Handle HTTP requests with error handling and retry logic."""
    
    def __init__(self, wifi_manager):
        """Initialize HTTP client with WiFi manager reference."""
        self.wifi = wifi_manager
        self.last_error = None
    
    def get_json(self, url, headers=None):
        """
        Fetch JSON from URL with error handling.
        Returns dict on success, None on failure.
        """
        if headers is None:
            headers = Config.HTTP_HEADERS
        
        try:
            if not self.wifi.is_online():
                log_warning("Not online, attempting reconnect")
                self.wifi.reconnect()
            
            debug_print(f"Fetching: {url}")
            response = requests.get(url=url, headers=headers)
            
            try:
                data = response.json()
                debug_print(f"Successfully fetched JSON ({len(str(data))} chars)")
                return data
            except ValueError as e:
                log_error("Invalid JSON in response", e)
                self.last_error = "invalid_json"
                return None
                
        except requests.OutOfRetries:
            log_error("HTTP request timeout/retries exhausted")
            self.last_error = "timeout"
            self.wifi.reconnect()
            return None
        except (RuntimeError, OSError, HttpError) as e:
            log_error("HTTP request failed", e)
            self.last_error = str(e)
            self.wifi.reconnect()
            return None
    
    def get_chunked(self, url, chunk_callback, chunk_size=1024, headers=None):
        """
        Fetch response in chunks, calling callback for each chunk.
        Callback receives (chunk_data, is_final) and should return True to continue.
        Returns total bytes received on success, -1 on failure.
        """
        if headers is None:
            headers = Config.HTTP_HEADERS
        
        try:
            if not self.wifi.is_online():
                log_warning("Not online, attempting reconnect")
                self.wifi.reconnect()
            
            debug_print(f"Fetching chunked: {url}")
            response = requests.get(url=url, headers=headers)
            
            total_bytes = 0
            for chunk in response.iter_content(chunk_size=chunk_size):
                w.feed()  # Feed watchdog
                total_bytes += len(chunk)
                
                should_continue = chunk_callback(chunk, False)
                if not should_continue:
                    break
            
            # Signal end of chunks
            chunk_callback(b'', True)
            
            debug_print(f"Chunked fetch complete: {total_bytes} bytes")
            return total_bytes
            
        except requests.OutOfRetries:
            log_error("HTTP chunked request timeout")
            self.last_error = "timeout"
            self.wifi.reconnect()
            return -1
        except (RuntimeError, OSError, HttpError) as e:
            log_error("HTTP chunked request failed", e)
            self.last_error = str(e)
            self.wifi.reconnect()
            return -1
