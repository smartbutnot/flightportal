"""
FlightPortal - Main Application
Displays information about aircraft flying overhead on an RGB matrix panel.

This is the modularized version with separated concerns:
- config.py: Configuration management
- network.py: WiFi and HTTP handling
- parser.py: JSON parsing with defensive extraction
- display.py: Matrix display rendering and animations
- flight_tracker.py: Core flight detection logic
- utils.py: Helper utilities
"""

import time
import gc
from microcontroller import watchdog as w
from watchdog import WatchDogMode

# Configure watchdog
w.timeout = 16  # seconds
w.mode = WatchDogMode.RESET

# Import all modules
from config import Config
from network import WiFiManager, HTTPClient
from display import DisplayManager
from flight_tracker import FlightTracker
from utils import (
    set_debug, log_info, log_warning, log_error, 
    print_memory_status, collect_garbage
)



class FlightPortalApp:
    """Main application controller."""
    
    def __init__(self):
        """Initialize the FlightPortal application."""
        log_info("========== FlightPortal Starting ==========")
        
        # Initialize subsystems
        self.display = DisplayManager()
        self.wifi = WiFiManager()
        self.http = HTTPClient(self.wifi)
        self.tracker = FlightTracker(self.http)
        
        # Application state
        self.loop_count = 0
        self.query_timer = 0
        self.last_error = None
        
        log_info("FlightPortal initialized successfully")
        print_memory_status()
    
    def startup(self):
        """Perform startup sequence."""
        log_info("Starting up...")
        
        # Connect to WiFi
        self.display.show_status("Connecting...")
        if not self.wifi.connect():
            self.display.show_error('wifi')
            log_error("Failed to connect to WiFi on startup")
            # Continue anyway - will retry in main loop
        else:
            self.display.clear_all_labels()
        
        log_info("Startup complete")
    
    def run_once(self):
        """Execute one iteration of the main loop."""
        self.loop_count += 1
        w.feed()
        
        # Check memory periodically
        if self.loop_count % 50 == 0:
            print_memory_status()
        
        # Search for flights
        flight_id = self.tracker.search_for_flights()
        w.feed()
        
        if flight_id:
            log_info(f"Flight found: {flight_id}")
            
            # Process the flight
            success, display_data = self.tracker.process_new_flight(flight_id)

            if success and display_data:
                # New flight detected
                # Phase 2: restore normal colors in case we were showing an error
                self.display.restore_label_colors()
                # Phase 2: animate plane with airline livery color
                plane_color = display_data.get('plane_color')
                self.display.animate_plane(plane_color)
                self.display.display_flight(display_data)
            elif success and not display_data:
                # Same flight - keep current display
                log_info("Same flight, continuing display")
            else:
                # Error processing flight
                log_error("Error processing flight, clearing display")
                self.display.clear_all_labels()
        else:
            # No flights found
            self.display.clear_all_labels()
        
        w.feed()
        
        # Query delay (check for flights every QUERY_DELAY seconds)
        # Break into 5-second chunks to feed watchdog more frequently
        for i in range(0, Config.QUERY_DELAY, 5):
            time.sleep(5)
            w.feed()
        
        collect_garbage()
    
    def run(self):
        """Run the main application loop."""
        self.startup()
        
        try:
            while True:
                self.run_once()
        except KeyboardInterrupt:
            log_info("Interrupted by user")
        except Exception as e:
            log_error("Unhandled exception in main loop", e)
            self.display.show_error('error')
        finally:
            log_info("========== FlightPortal Shutting Down ==========")


# Application entry point
if __name__ == "__main__":
    app = FlightPortalApp()
    app.run()
