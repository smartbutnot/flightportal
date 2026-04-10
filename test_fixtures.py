"""
Test fixtures for FlightPortal parser testing.
Contains sample Flightradar24 API responses for offline testing.
"""

# Example flight search response (minimal)
FR24_SEARCH_RESPONSE_EXAMPLE = {
    "version": [3, 1, 1],
    "full_count": 1,
    "3c6421": [
        "3c6421", 55.1234, -120.5678, 340, 28000, 420, "0", "B737", "N12345", "KJFK", "KLAX", "", 1234567890, "extrafield"
    ]
}

# Example flight search with no flights
FR24_SEARCH_RESPONSE_EMPTY = {
    "version": [3, 1, 1],
    "full_count": 0
}

# Simplified flight details response (truncated at trail marker)
# This represents what gets loaded after chunked fetch and truncation
FR24_DETAILS_JSON_EXAMPLE = """{
"identification": {
    "number": {
        "default": "BA1234"
    },
    "callsign": "BAW1234"
},
"aircraft": {
    "model": {
        "code": "B737",
        "text": "Boeing 737-800"
    }
},
"airline": {
    "name": "British Airways"
},
"airport": {
    "origin": {
        "name": "London Heathrow Airport",
        "code": {
            "iata": "LHR"
        }
    },
    "destination": {
        "name": "Los Angeles International Airport",
        "code": {
            "iata": "LAX"
        }
    }
},
"trail": [
    {
        "lat": 55.1234,
        "lng": -120.5678,
        "alt": 28000,
        "spd": 420,
        "hd": 260
    }
]}"""

# Another example with different airline
FR24_DETAILS_JSON_EXAMPLE_2 = """{
"identification": {
    "number": {
        "default": "AA456"
    },
    "callsign": "AAL456"
},
"aircraft": {
    "model": {
        "code": "A380",
        "text": "Airbus A380-800"
    }
},
"airline": {
    "name": "American Airlines"
},
"airport": {
    "origin": {
        "name": "New York Kennedy Airport",
        "code": {
            "iata": "JFK"
        }
    },
    "destination": {
        "name": "London Heathrow Airport",
        "code": {
            "iata": "LHR"
        }
    }
},
"trail": [
    {
        "lat": 40.6413,
        "lng": -73.7781,
        "alt": 35000,
        "spd": 480,
        "hd": 90
    }
]}"""

# Example with missing optional fields (defensive parsing test)
FR24_DETAILS_JSON_MINIMAL = """{
"identification": {
    "number": {
        "default": "XY999"
    },
    "callsign": "XYZ999"
},
"aircraft": {
    "model": {
        "code": "CRJ",
        "text": "Bombardier CRJ-700"
    }
},
"airline": {
    "name": "Regional Carrier"
},
"airport": {
    "origin": {
        "name": "Small Regional Airport",
        "code": {
            "iata": "SMA"
        }
    },
    "destination": {
        "name": "Another Regional Airport",
        "code": {
            "iata": "ARM"
        }
    }
},
"trail": [
    {
        "lat": 42.1234,
        "lng": -74.5678,
        "alt": 15000,
        "spd": 350,
        "hd": 180
    }
]}"""

# Invalid JSON test case
FR24_DETAILS_JSON_MALFORMED = """{
"identification": {
    "number": {
        "default": "BAD001"
    },
    INVALID_SYNTAX: true,
    "callsign": "BAD001"
},
...truncated...
}"""


class FlightFixtures:
    """Helper class for accessing test fixtures."""
    
    SEARCH_RESPONSES = {
        'success': FR24_SEARCH_RESPONSE_EXAMPLE,
        'empty': FR24_SEARCH_RESPONSE_EMPTY,
    }
    
    DETAIL_RESPONSES = {
        'normal_1': FR24_DETAILS_JSON_EXAMPLE,
        'normal_2': FR24_DETAILS_JSON_EXAMPLE_2,
        'minimal': FR24_DETAILS_JSON_MINIMAL,
        'malformed': FR24_DETAILS_JSON_MALFORMED,
    }
    
    @staticmethod
    def get_search_response(key):
        """Get a search response fixture by key."""
        return FlightFixtures.SEARCH_RESPONSES.get(key)
    
    @staticmethod
    def get_detail_response(key):
        """Get a detail response fixture by key."""
        return FlightFixtures.DETAIL_RESPONSES.get(key)
    
    @staticmethod
    def get_all_search_keys():
        """Get list of available search response keys."""
        return list(FlightFixtures.SEARCH_RESPONSES.keys())
    
    @staticmethod
    def get_all_detail_keys():
        """Get list of available detail response keys."""
        return list(FlightFixtures.DETAIL_RESPONSES.keys())
