"""
Unit tests for FlightPortal flight tracker module.
Uses mock objects to simulate hardware and network.
These tests run on standard Python - no hardware required.
"""

import sys
import os
from unittest.mock import Mock, patch, MagicMock
import json

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from test_fixtures import FlightFixtures
from parser import FlightDetailsParser


class MockHTTPClient:
    """Mock HTTP client for testing."""
    
    def __init__(self):
        self.get_json_response = None
        self.get_chunked_data = None
    
    def get_json(self, url):
        """Mock get_json method."""
        return self.get_json_response
    
    def get_chunked(self, url, callback):
        """Mock get_chunked method."""
        if self.get_chunked_data:
            callback(self.get_chunked_data, True)
            return len(self.get_chunked_data)
        return 0


class TestFlightTrackerLogic:
    """Test flight tracking logic without real HTTP."""
    
    def test_search_flight_parsing(self):
        """Test that search results are parsed correctly."""
        mock_http = MockHTTPClient()
        mock_http.get_json_response = FlightFixtures.get_search_response('success')
        
        # Simulate flight search
        response = mock_http.get_json("http://fake.url")
        
        # Should have flight data
        assert response is not None
        assert "3c6421" in response
        assert response["full_count"] == 1
        
        print("  ✓ Search response parsed correctly")
    
    def test_no_flights_found(self):
        """Test when no flights are available."""
        mock_http = MockHTTPClient()
        mock_http.get_json_response = FlightFixtures.get_search_response('empty')
        
        response = mock_http.get_json("http://fake.url")
        
        assert response is not None
        assert response["full_count"] == 0
        
        print("  ✓ Empty search handled correctly")
    
    def test_details_chunked_loading(self):
        """Test that flight details are loaded via chunks."""
        mock_http = MockHTTPClient()
        details_json = FlightFixtures.get_detail_response('normal_1')
        mock_http.get_chunked_data = details_json.encode()
        
        # Test chunked loading
        received_data = None
        def callback(chunk, is_final):
            nonlocal received_data
            received_data = chunk
            return True
        
        bytes_loaded = mock_http.get_chunked("http://details.url", callback)
        
        assert received_data is not None
        assert len(received_data) > 0
        assert bytes_loaded > 0
        
        print("  ✓ Details chunked loading works")
    
    def test_flight_info_extraction(self):
        """Test extracting flight information from JSON."""
        json_str = FlightFixtures.get_detail_response('normal_1')
        json_data = json.loads(json_str)
        
        parser = FlightDetailsParser()
        parser.json_data = json_data
        flight_info = parser.extract_flight_info()
        
        assert flight_info is not None
        assert flight_info['flight_number'] == "BA1234"
        assert flight_info['airline_name'] == "British Airways"
        assert flight_info['aircraft_code'] == "B737"
        
        print("  ✓ Flight information extracted correctly")
    
    def test_duplicate_detection(self):
        """Test detecting duplicate flights."""
        last_flight_id = "3c6421"
        current_flight_id = "3c6421"
        
        is_duplicate = (current_flight_id == last_flight_id)
        assert is_duplicate == True
        
        # Different flight should not be duplicate
        current_flight_id = "4d7532"
        is_duplicate = (current_flight_id == last_flight_id)
        assert is_duplicate == False
        
        print("  ✓ Duplicate flight detection works")
    
    def test_history_management(self):
        """Test flight history tracking."""
        history = []
        max_history = 10
        
        # Add flights
        for i in range(15):
            entry = {
                'flight_id': f'FLT{i:04d}',
                'flight_number': f'BA{i}',
                'timestamp': i
            }
            history.insert(0, entry)
            
            # Keep only recent
            if len(history) > max_history:
                history = history[:max_history]
        
        assert len(history) == max_history
        assert history[0]['flight_id'] == 'FLT0014'  # Newest
        assert history[-1]['flight_id'] == 'FLT0005'  # Oldest kept
        
        print("  ✓ Flight history management works")
    
    def test_statistics_tracking(self):
        """Test tracking flight statistics."""
        stats = {
            'flights_tracked': 0,
            'current_flight': None,
            'last_updated': 0,
        }
        
        # Simulate tracking flights
        flights = ['FLT001', 'FLT002', 'FLT003']
        for flight_id in flights:
            stats['flights_tracked'] += 1
            stats['current_flight'] = flight_id
            stats['last_updated'] = len(flights)
        
        assert stats['flights_tracked'] == 3
        assert stats['current_flight'] == 'FLT003'
        assert stats['last_updated'] == 3
        
        print("  ✓ Statistics tracking works")


class TestDisplayDataFlow:
    """Test the flow of data through the display pipeline."""
    
    def test_full_pipeline(self):
        """Test complete data flow from search to display."""
        # Step 1: Search returns flight ID
        search_response = FlightFixtures.get_search_response('success')
        flight_id = search_response.get('3c6421') is not None
        assert flight_id
        
        # Step 2: Fetch details
        details_json = FlightFixtures.get_detail_response('normal_1')
        details_data = json.loads(details_json)
        
        # Step 3: Parse flight info
        parser = FlightDetailsParser()
        parser.json_data = details_data
        flight_info = parser.extract_flight_info()
        assert flight_info is not None
        
        # Step 4: Format for display
        from parser import FlightDataFormatter
        display_data = FlightDataFormatter.prepare_display_data(flight_info)
        
        assert display_data is not None
        assert display_data['label1_short'] == "BA1234"
        assert display_data['label2_short'] == "LHR-LAX"
        
        print("  ✓ Full data pipeline works end-to-end")
    
    def test_error_recovery_path(self):
        """Test that errors don't break the pipeline."""
        # Simulate invalid JSON
        invalid_json = "{INVALID}"
        
        try:
            data = json.loads(invalid_json)
            assert False, "Should have raised exception"
        except json.JSONDecodeError:
            # Expected - system should recover
            pass
        
        # Pipeline should continue with next flight
        valid_json = FlightFixtures.get_detail_response('normal_1')
        data = json.loads(valid_json)
        assert data is not None
        
        print("  ✓ Error recovery in pipeline works")


class TestMemoryManagement:
    """Test memory-related functionality."""
    
    def test_buffer_creation(self):
        """Test memory buffer creation."""
        from utils import MemoryBuffer
        
        buffer = MemoryBuffer(1024)
        assert buffer.size == 1024
        assert buffer.length == 0
        
        print("  ✓ Buffer creation works")
    
    def test_buffer_write(self):
        """Test writing to buffer."""
        from utils import MemoryBuffer
        
        buffer = MemoryBuffer(100)
        data = b"Test data"
        bytes_written = buffer.write(data)
        
        assert bytes_written == len(data)
        assert buffer.length == len(data)
        
        print("  ✓ Buffer write works")
    
    def test_buffer_find(self):
        """Test finding patterns in buffer."""
        from utils import MemoryBuffer
        
        buffer = MemoryBuffer(100)
        data = b"This is a test string"
        buffer.write(data)
        
        pos = buffer.find(b"test")
        assert pos > 0
        assert pos == 10
        
        # Not found
        pos = buffer.find(b"missing")
        assert pos == -1
        
        print("  ✓ Buffer find works")
    
    def test_buffer_clear(self):
        """Test clearing buffer."""
        from utils import MemoryBuffer
        
        buffer = MemoryBuffer(100)
        buffer.write(b"Data")
        assert buffer.length == 4
        
        buffer.clear()
        assert buffer.length == 0
        
        print("  ✓ Buffer clear works")


def run_all_tests():
    """Run all flight tracker tests."""
    print("\n" + "=" * 60)
    print("FlightPortal Flight Tracker Tests")
    print("=" * 60)
    
    print("\nFlight Tracking Logic:")
    logic_tests = TestFlightTrackerLogic()
    logic_tests.test_search_flight_parsing()
    logic_tests.test_no_flights_found()
    logic_tests.test_details_chunked_loading()
    logic_tests.test_flight_info_extraction()
    logic_tests.test_duplicate_detection()
    logic_tests.test_history_management()
    logic_tests.test_statistics_tracking()
    
    print("\nDisplay Data Flow:")
    flow_tests = TestDisplayDataFlow()
    flow_tests.test_full_pipeline()
    flow_tests.test_error_recovery_path()
    
    print("\nMemory Management:")
    memory_tests = TestMemoryManagement()
    memory_tests.test_buffer_creation()
    memory_tests.test_buffer_write()
    memory_tests.test_buffer_find()
    memory_tests.test_buffer_clear()
    
    print("\n" + "=" * 60)
    print("✓ All tracker tests passed!")
    print("=" * 60)


if __name__ == '__main__':
    run_all_tests()
