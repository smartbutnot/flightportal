"""
Unit tests for FlightPortal parser module.
These tests run on standard Python - no hardware required.
"""

import json
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from test_fixtures import FlightFixtures
from parser import FlightSearchParser, FlightDetailsParser, FlightDataFormatter


class TestFlightSearchParser:
    """Test the flight search response parser."""
    
    def test_extract_flight_id_success(self):
        """Test extracting flight ID from valid search response."""
        fixture = FlightFixtures.get_search_response('success')
        parser = FlightSearchParser()
        flight_id = parser.extract_flight_id(fixture)
        
        assert flight_id == "3c6421", f"Expected 3c6421, got {flight_id}"
        print("  ✓ Extract flight ID from successful search")
    
    def test_extract_flight_id_empty(self):
        """Test with no flights found."""
        fixture = FlightFixtures.get_search_response('empty')
        parser = FlightSearchParser()
        flight_id = parser.extract_flight_id(fixture)
        
        assert flight_id is None, f"Expected None, got {flight_id}"
        print("  ✓ Handle empty search response")
    
    def test_extract_flight_id_invalid_input(self):
        """Test with invalid input types."""
        parser = FlightSearchParser()
        
        # Test with None
        result = parser.extract_flight_id(None)
        assert result is None
        
        # Test with invalid type
        result = parser.extract_flight_id("not a dict")
        assert result is None
        
        # Test with empty dict
        result = parser.extract_flight_id({})
        assert result is None
        
        print("  ✓ Handle invalid input gracefully")


class TestFlightDetailsParser:
    """Test the flight details parser."""
    
    def test_parse_normal_flight(self):
        """Test parsing a normal flight details response."""
        json_str = FlightFixtures.get_detail_response('normal_1')
        json_data = json.loads(json_str)
        
        parser = FlightDetailsParser()
        parser.json_data = json_data
        flight_info = parser.extract_flight_info()
        
        assert flight_info is not None
        assert flight_info['flight_number'] == "BA1234"
        assert flight_info['flight_callsign'] == "BAW1234"
        assert flight_info['airline_name'] == "British Airways"
        assert flight_info['aircraft_code'] == "B737"
        assert flight_info['airport_origin_code'] == "LHR"
        assert flight_info['airport_destination_code'] == "LAX"
        
        print("  ✓ Parse normal flight details")
    
    def test_parse_minimal_flight(self):
        """Test parsing with minimal data."""
        json_str = FlightFixtures.get_detail_response('minimal')
        json_data = json.loads(json_str)
        
        parser = FlightDetailsParser()
        parser.json_data = json_data
        flight_info = parser.extract_flight_info()
        
        assert flight_info is not None
        assert flight_info['flight_number'] == "XY999"
        
        print("  ✓ Handle minimal flight data")
    
    def test_parse_missing_fields(self):
        """Test that missing fields are handled gracefully."""
        # Create a minimal valid response
        minimal_json = {
            "identification": {
                "number": {"default": "TEST"},
                "callsign": "TEST123"
            },
            "aircraft": {"model": {"code": "DH4", "text": "Dash 8"}},
            "airline": {"name": "Test Airline"},
            "airport": {
                "origin": {"name": "Test Airport", "code": {"iata": "TST"}},
                "destination": {"name": "Another Airport", "code": {"iata": "AAA"}}
            }
        }
        
        parser = FlightDetailsParser()
        parser.json_data = minimal_json
        flight_info = parser.extract_flight_info()
        
        assert flight_info is not None
        assert flight_info['flight_number'] == "TEST"
        
        print("  ✓ Handle missing optional fields")
    
    def test_parse_no_data_loaded(self):
        """Test error when no JSON data is loaded."""
        parser = FlightDetailsParser()
        flight_info = parser.extract_flight_info()
        
        assert flight_info is None
        
        print("  ✓ Return None when no data loaded")


class TestFlightDataFormatter:
    """Test the display data formatter."""
    
    def test_format_normal_flight(self):
        """Test formatting normal flight data."""
        json_str = FlightFixtures.get_detail_response('normal_1')
        json_data = json.loads(json_str)
        
        parser = FlightDetailsParser()
        parser.json_data = json_data
        flight_info = parser.extract_flight_info()
        
        display_data = FlightDataFormatter.prepare_display_data(flight_info)
        
        assert display_data is not None
        assert display_data['label1_short'] == "BA1234"
        assert display_data['label1_long'] == "British Airways"
        assert display_data['label2_short'] == "LHR-LAX"
        
        # Phase 2: label3 shows altitude/speed (ROW3_MODE='alt_speed')
        # If trail data present: show altitude
        # label3_short will be either altitude or aircraft code as fallback
        assert display_data['label3_short'] is not None
        assert display_data['label3_long'] is not None
        
        # Phase 2: plane_color should be set (BA = British Airways blue)
        assert 'plane_color' in display_data
        assert display_data['plane_color'] == 0x0075C9  # BA blue
        
        print("  ✓ Format flight data for display")
    
    def test_format_with_none(self):
        """Test formatting when flight_info is None."""
        display_data = FlightDataFormatter.prepare_display_data(None)
        
        assert display_data is None
        
        print("  ✓ Handle None flight data")
    
    def test_format_second_flight(self):
        """Test formatting another example flight."""
        json_str = FlightFixtures.get_detail_response('normal_2')
        json_data = json.loads(json_str)
        
        parser = FlightDetailsParser()
        parser.json_data = json_data
        flight_info = parser.extract_flight_info()
        
        display_data = FlightDataFormatter.prepare_display_data(flight_info)
        
        assert display_data['label1_short'] == "AA456"
        assert display_data['label2_short'] == "JFK-LHR"
        # Phase 2: plane_color set for American Airlines
        assert 'plane_color' in display_data
        
        print("  ✓ Format different flight correctly")


def run_all_tests():
    """Run all parser tests."""
    print("\n" + "=" * 60)
    print("FlightPortal Parser Tests")
    print("=" * 60)
    
    print("\nFlight Search Parser:")
    search_tests = TestFlightSearchParser()
    search_tests.test_extract_flight_id_success()
    search_tests.test_extract_flight_id_empty()
    search_tests.test_extract_flight_id_invalid_input()
    
    print("\nFlight Details Parser:")
    details_tests = TestFlightDetailsParser()
    details_tests.test_parse_normal_flight()
    details_tests.test_parse_minimal_flight()
    details_tests.test_parse_missing_fields()
    details_tests.test_parse_no_data_loaded()
    
    print("\nFlight Data Formatter:")
    formatter_tests = TestFlightDataFormatter()
    formatter_tests.test_format_normal_flight()
    formatter_tests.test_format_with_none()
    formatter_tests.test_format_second_flight()
    
    print("\n" + "=" * 60)
    print("✓ All parser tests passed!")
    print("=" * 60)


if __name__ == '__main__':
    run_all_tests()
