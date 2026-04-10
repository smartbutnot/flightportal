"""
Core flight tracking logic for FlightPortal.
Handles flight detection, deduplication, and history.
"""

import gc
import time
from config import Config
from utils import log_error, log_info, debug_print, collect_garbage, MemoryBuffer
from network import HTTPClient
from parser import FlightSearchParser, FlightDetailsParser, FlightDataFormatter


class FlightTracker:
    """Track and manage flight detection."""
    
    def __init__(self, http_client):
        """Initialize flight tracker with HTTP client."""
        self.http = http_client
        self.last_flight_id = None
        self.last_display_time = 0
        
        # Flight history (keep last N flights)
        self.history = []
        self.max_history = 10
        
        # Parsers
        self.search_parser = FlightSearchParser()
        self.details_parser = FlightDetailsParser()
        self.formatter = FlightDataFormatter()
        
        log_info("Flight tracker initialized")
    
    def search_for_flights(self):
        """
        Search for flights in the configured bounds box.
        Returns flight_id on success, None if no flights found.
        """
        url = f"{Config.FR24_SEARCH_HEAD}{Config.BOUNDS_BOX}{Config.FR24_SEARCH_TAIL}"
        
        debug_print(f"Searching for flights at {url[:50]}...")
        
        response = self.http.get_json(url)
        if response is None:
            log_error("Failed to get flight search response")
            return None
        
        flight_id = self.search_parser.extract_flight_id(response)
        return flight_id
    
    def fetch_flight_details(self, flight_id):
        """
        Fetch detailed information for a flight ID.
        Returns flight_info dict on success, None on failure.
        """
        url = f"{Config.FR24_DETAILS_HEAD}{flight_id}"
        
        log_info(f"Fetching details for flight {flight_id}")
        
        # Create a fresh memory buffer for this flight
        buffer = MemoryBuffer(Config.JSON_BUFFER_SIZE)
        
        def chunk_handler(chunk, is_final):
            """Handle incoming chunks."""
            if is_final:
                return True
            
            try:
                # Check for trail marker
                if buffer.length > 0:
                    trail_pos = buffer.find(b'"trail":')
                    if trail_pos >= 0:
                        debug_print(f"Found trail marker at {trail_pos}")
                        # Find first closing brace after trail
                        search_start = trail_pos + len(b'"trail":')
                        for i in range(search_start, buffer.length):
                            if buffer.buffer[i:i+1] == b'}':
                                # Truncate and close JSON
                                buffer.truncate_at(i + 1)
                                buffer.write(b']}', buffer.length)
                                return False
                        return True
                
                # Write chunk to buffer
                buffer.write(chunk, buffer.length)
                return True
                
            except MemoryError:
                log_error(f"Buffer overflow at {buffer.length} bytes")
                return False
        
        # Fetch with chunking
        bytes_read = self.http.get_chunked(url, chunk_handler)
        
        if bytes_read < 0:
            log_error("Failed to fetch flight details")
            return None
        
        # Parse the buffer
        if not self.details_parser.load_from_buffer(buffer.get_bytes()):
            log_error("Failed to parse flight JSON")
            return None
        
        # Extract flight information
        flight_info = self.details_parser.extract_flight_info()
        if not flight_info:
            log_error("Failed to extract flight information")
            return None
        
        collect_garbage()
        return flight_info
    
    def get_display_data(self, flight_info):
        """Convert flight info to display data."""
        if not flight_info:
            return None
        
        display_data = self.formatter.prepare_display_data(flight_info)
        return display_data
    
    def is_duplicate_flight(self, flight_id):
        """Check if this flight ID was recently displayed."""
        is_dup = flight_id == self.last_flight_id
        if is_dup:
            debug_print(f"Duplicate flight detected: {flight_id}")
        return is_dup
    
    def process_new_flight(self, flight_id):
        """
        Process a newly detected flight.
        Returns (success: bool, display_data: dict or None)
        """
        if self.is_duplicate_flight(flight_id):
            return (True, None)  # Continue showing current flight
        
        log_info(f"New flight detected: {flight_id}")
        
        # Fetch flight details
        flight_info = self.fetch_flight_details(flight_id)
        if not flight_info:
            return (False, None)
        
        # Get display data
        display_data = self.get_display_data(flight_info)
        if not display_data:
            return (False, None)
        
        # Update tracker state
        self.last_flight_id = flight_id
        self.last_display_time = time.time()
        
        # Add to history
        self._add_to_history(flight_id, flight_info)
        
        return (True, display_data)
    
    def _add_to_history(self, flight_id, flight_info):
        """Add flight to history."""
        entry = {
            'flight_id': flight_id,
            'flight_number': flight_info.get('flight_number'),
            'timestamp': time.time()
        }
        self.history.insert(0, entry)
        
        # Keep only recent flights
        if len(self.history) > self.max_history:
            self.history = self.history[:self.max_history]
        
        log_info(f"Added to history. Total flights tracked: {len(self.history)}")
    
    def get_history(self):
        """Get flight history."""
        return self.history
    
    def clear_history(self):
        """Clear flight history."""
        self.history = []
        log_info("Flight history cleared")
    
    def get_stats(self):
        """Get tracking statistics."""
        return {
            'flights_tracked': len(self.history),
            'current_flight': self.last_flight_id,
            'last_updated': self.last_display_time,
        }
