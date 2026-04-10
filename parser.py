"""
JSON parsing for Flightradar24 API responses.
Provides defensive extraction with graceful handling of API changes.
"""

import json
import gc
from config import Config
from utils import (
    MemoryBuffer, log_error, log_info, debug_print, collect_garbage
)


class FlightSearchParser:
    """Parse flight search results from FR24 API."""
    
    @staticmethod
    def extract_flight_id(response_dict):
        """
        Extract a single flight ID from search response.
        Returns flight_id on success, None on failure.
        
        FR24 response format:
        {
            "version": [...],
            "full_count": number,
            "FLIGHT_ID": [data_array],
            ...
        }
        """
        try:
            if not isinstance(response_dict, dict):
                log_error("Search response is not a dictionary")
                return None
            
            # Response should have exactly 3+ main keys (version, full_count, flight_id(s))
            if len(response_dict) < 3:
                debug_print(f"Search response has only {len(response_dict)} keys, no flights found")
                return None
            
            # Find flights (anything that's not metadata)
            for flight_id, flight_info in response_dict.items():
                # Skip metadata fields
                if flight_id in ("version", "full_count"):
                    continue
                
                # Validate flight_info is a list/dict with enough data
                # It could be a list (legacy) or dict (newer format)
                try:
                    if isinstance(flight_info, (list, tuple)):
                        # Legacy array format - check length
                        if len(flight_info) > 13:
                            debug_print(f"Found flight (array): {flight_id}")
                            return flight_id
                    elif isinstance(flight_info, dict):
                        # Dict format - check that it has required fields
                        if len(flight_info) > 0:
                            debug_print(f"Found flight (dict): {flight_id}")
                            return flight_id
                except (TypeError, AttributeError):
                    continue
            
            debug_print("No valid flights in search response")
            return None
            
        except Exception as e:
            log_error("Error extracting flight ID from search response", e)
            return None


class FlightDetailsParser:
    """Parse detailed flight information from FR24 API with chunked loading."""
    
    # Fields to extract from flight details JSON
    EXTRACTABLE_FIELDS = {
        'flight_number':          ['identification', 'number', 'default'],
        'flight_callsign':        ['identification', 'callsign'],
        'aircraft_code':          ['aircraft', 'model', 'code'],
        'aircraft_model':         ['aircraft', 'model', 'text'],
        'airline_name':           ['airline', 'name'],
        'airport_origin_name':    ['airport', 'origin', 'name'],
        'airport_origin_code':    ['airport', 'origin', 'code', 'iata'],
        'airport_destination_name': ['airport', 'destination', 'name'],
        'airport_destination_code': ['airport', 'destination', 'code', 'iata'],
        # Phase 2: altitude, speed, heading from first trail entry
        'altitude':               ['trail', 0, 'alt'],
        'speed':                  ['trail', 0, 'spd'],
        'heading':                ['trail', 0, 'hd'],
    }
    
    def __init__(self):
        """Initialize the parser with a memory buffer."""
        self.buffer = MemoryBuffer(Config.JSON_BUFFER_SIZE)
        self.json_data = None
    
    def load_chunked(self, http_client):
        """
        Load flight details in chunks, truncating at the 'trail' section.
        
        Returns True on success, False on failure.
        """
        self.buffer.clear()
        
        # Callback to process chunks
        def chunk_handler(chunk, is_final):
            if is_final:
                return True
            
            try:
                # Try to write chunk to buffer
                self.buffer.write(chunk, self.buffer.length)
                
                # Check if we've found the trail marker (which marks end of needed data)
                trail_pos = self.buffer.find(b'"trail":')
                if trail_pos >= 0:
                    debug_print(f"Found trail marker at position {trail_pos}")
                    
                    # Find the first closing brace after trail marker
                    search_start = trail_pos + len(b'"trail":')
                    trail_data = bytes(self.buffer.buffer[search_start:])
                    
                    first_brace = trail_data.find(b'}')
                    if first_brace >= 0:
                        # Truncate at this point and add closing braces
                        truncate_pos = search_start + first_brace + 1
                        self.buffer.truncate_at(truncate_pos)
                        
                        # Add closing braces to complete JSON
                        self.buffer.write(b']}', self.buffer.length)
                        
                        log_info(f"Truncated JSON buffer at {self.buffer.length} bytes")
                        return False  # Stop reading chunks
                
                return True  # Continue reading
                
            except MemoryError:
                log_error(f"Buffer full at {self.buffer.length} bytes")
                return False
        
        # Use HTTP client to fetch with chunking
        url = Config.FR24_DETAILS_HEAD  # Note: flight ID will be appended by caller
        
        # This is a helper - the actual URL building happens in caller
        return True  # Placeholder
    
    def load_from_buffer(self, buffer_bytes):
        """Load and parse JSON from a byte buffer."""
        try:
            collect_garbage()
            
            # Decode and parse JSON
            json_str = buffer_bytes.decode('utf-8', errors='ignore')
            debug_print(f"Parsing JSON ({len(json_str)} chars)")
            
            self.json_data = json.loads(json_str)
            log_info("Successfully parsed flight details JSON")
            return True
            
        except ValueError as e:
            log_error("Invalid JSON in flight details", e)
            return False
        except Exception as e:
            log_error("Unexpected error parsing JSON", e)
            return False
    
    def extract_flight_info(self):
        """
        Extract relevant flight information from parsed JSON.
        Returns dict with flight details on success, None on failure.
        """
        if not self.json_data:
            log_error("No JSON data loaded")
            return None
        
        flight_info = {}
        
        # Safely extract each field
        for field_name, path in self.EXTRACTABLE_FIELDS.items():
            try:
                value = self.json_data
                for key in path:
                    value = value[key]
                
                # Clean up some values
                if field_name.endswith('_name'):
                    value = value.replace(" Airport", "")
                
                flight_info[field_name] = value
                
            except (KeyError, TypeError):
                # Field not found - set to None or empty string
                flight_info[field_name] = None
                debug_print(f"Field not found: {field_name}")
        
        # Validate we have at least some meaningful data
        if not any(flight_info.values()):
            log_error("No valid flight information extracted")
            return None
        
        log_info(f"Extracted flight: {flight_info.get('flight_number', 'UNKNOWN')}")
        return flight_info


class FlightDataFormatter:
    """Format extracted flight data for display."""

    @staticmethod
    def _get_airline_plane_color(flight_info):
        """Return a plane animation color matching the airline livery."""
        # Try flight number prefix first (e.g. 'BA' from 'BA1234')
        flight_number = flight_info.get('flight_number') or ''
        callsign = flight_info.get('flight_callsign') or ''

        for prefix in (flight_number[:3], flight_number[:2], callsign[:3], callsign[:2]):
            if prefix and prefix in Config.AIRLINE_COLORS:
                return Config.AIRLINE_COLORS[prefix]

        return Config.DEFAULT_PLANE_COLOR

    @staticmethod
    def prepare_display_data(flight_info):
        """
        Convert flight_info dict to display labels.
        Returns dict with label1_short, label1_long, etc.
        Phase 2: includes plane_color and row3 alt/speed data.
        """
        if not flight_info:
            return None

        display_data = {}

        # Row 1: Flight number / Airline
        display_data['label1_short'] = flight_info.get('flight_number') or ''
        display_data['label1_long']  = flight_info.get('airline_name') or ''

        # Row 2: Airport codes / Names
        origin = flight_info.get('airport_origin_code') or 'UNK'
        dest   = flight_info.get('airport_destination_code') or 'UNK'
        display_data['label2_short'] = f"{origin}-{dest}"

        origin_name = flight_info.get('airport_origin_name') or origin
        dest_name   = flight_info.get('airport_destination_name') or dest
        display_data['label2_long'] = f"{origin_name}-{dest_name}"

        # Row 3: Aircraft code/model OR altitude+speed depending on ROW3_MODE
        if Config.ROW3_MODE == 'alt_speed':
            alt   = flight_info.get('altitude')
            speed = flight_info.get('speed')
            if alt is not None and speed is not None:
                display_data['label3_short'] = f"{alt}ft"
                display_data['label3_long']  = f"{alt}ft {speed}kts"
            else:
                # Fallback to aircraft if trail data missing
                display_data['label3_short'] = flight_info.get('aircraft_code') or ''
                display_data['label3_long']  = flight_info.get('aircraft_model') or ''
        else:
            display_data['label3_short'] = flight_info.get('aircraft_code') or ''
            display_data['label3_long']  = flight_info.get('aircraft_model') or ''

        # Phase 2: Airline tail logo color for plane animation
        display_data['plane_color'] = FlightDataFormatter._get_airline_plane_color(flight_info)

        return display_data
