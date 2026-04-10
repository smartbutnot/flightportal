"""
Configuration management for FlightPortal.
Loads and validates settings from secrets.py and provides runtime configuration.
"""

import json

# Attempt to load secrets
try:
    from secrets import secrets
except ImportError:
    print("ERROR: Secrets including geo are kept in secrets.py, please add them there!")
    raise

class Config:
    """Central configuration object for FlightPortal."""
    
    # Display settings
    DISPLAY_ROTATION = 0
    DISPLAY_DEBUG = False
    
    # Color palette (RGB hex values)
    COLORS = {
        'row_one':    0xEE82EE,   # Magenta  - flight number
        'row_two':    0x4B0082,   # Indigo   - route
        'row_three':  0xFFA500,   # Orange   - aircraft
        'plane':      0x4B0082,   # Indigo   - plane animation (default)
        'error_wifi': 0xFF0000,   # Red      - WiFi error
        'error_api':  0xFF8800,   # Orange   - API error
        'status_ok':  0x00FF00,   # Green    - OK
        'alt_speed':  0x00FF88,   # Cyan-green - Phase 2: altitude/speed row
    }

    # Phase 2: Airline tail logo colors (IATA prefix -> hex color)
    # Plane animation uses this color for the matching airline
    AIRLINE_COLORS = {
        'BA':  0x0075C9,   # British Airways - blue
        'EZY': 0xFF6600,   # EasyJet - orange
        'RYR': 0x003087,   # Ryanair - dark blue
        'BAW': 0x0075C9,   # BA callsign
        'EZS': 0xFF6600,   # EasyJet callsign
        'AAL': 0xC8102E,   # American Airlines - red
        'UAL': 0x005DAA,   # United - blue
        'DAL': 0xC01933,   # Delta - red
        'SWA': 0xF4821F,   # Southwest - orange
        'DLH': 0xFFCC00,   # Lufthansa - yellow
        'AFR': 0x002395,   # Air France - blue
        'KLM': 0x00A1DE,   # KLM - light blue
        'UAE': 0xC60C30,   # Emirates - red
        'THY': 0xC8102E,   # Turkish - red
        'SIA': 0x003087,   # Singapore - blue
        'QFA': 0xFF0000,   # Qantas - red
        'VIR': 0xC0001A,   # Virgin Atlantic - red
    }
    DEFAULT_PLANE_COLOR = 0x4B0082  # Fallback indigo if airline not in map

    # Animation and timing (in seconds)
    TIMINGS = {
        'query_delay': 30,
        'pause_between_scrolls': 3,
        'plane_animation_speed': 0.04,
        'text_scroll_speed': 0.04,
        'connection_check_delay': 5,
    }

    # Phase 2: Brightness auto-adjust (24h schedule)
    # Entries: (start_hour, end_hour, brightness_0_to_1)
    # Evaluated in order; first matching window wins
    BRIGHTNESS_SCHEDULE = [
        (0,  6,  0.10),   # midnight-6am: 10% - very dim
        (6,  8,  0.30),   # 6-8am: 30% - dawn
        (8,  20, 1.00),   # 8am-8pm: full brightness
        (20, 22, 0.50),   # 8-10pm: 50%
        (22, 24, 0.20),   # 10pm-midnight: 20%
    ]
    BRIGHTNESS_DEFAULT = 0.20   # Fallback if schedule unused
    BRIGHTNESS_ENABLED = True   # Set False to always use full brightness

    # Phase 2: Error display settings
    ERROR_DISPLAY_DURATION = 10  # seconds to show error before retrying
    ERROR_BLINK_SPEED = 0.5      # blink interval for error indicator bar

    # Phase 2: Row 3 display mode
    # 'aircraft'  -> original: aircraft code / model (e.g. B737 / Boeing 737)
    # 'alt_speed' -> altitude (ft) and speed (kts) from trail entry
    ROW3_MODE = 'alt_speed'
    
    # Network/API settings
    QUERY_DELAY = 30  # seconds between FR24 queries
    
    # Flightradar24 API configuration
    FR24_SEARCH_HEAD = "https://data-cloud.flightradar24.com/zones/fcgi/feed.js?bounds="
    FR24_SEARCH_TAIL = "&faa=1&satellite=1&mlat=1&flarm=1&adsb=1&gnd=0&air=1&vehicles=0&estimated=0&maxage=14400&gliders=0&stats=0&ems=1&limit=1"
    FR24_DETAILS_HEAD = "https://data-live.flightradar24.com/clickhandler/?flight="
    
    # HTTP request headers
    HTTP_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0",
        "cache-control": "no-store, no-cache, must-revalidate, post-check=0, pre-check=0",
        "accept": "application/json"
    }
    
    # Memory settings
    JSON_BUFFER_SIZE = 14336  # Size of static JSON byte buffer
    JSON_CHUNK_SIZE = 1024    # Size of chunks to read from HTTP response
    
    # Watchdog settings (in seconds)
    WATCHDOG_TIMEOUT = 16
    
    # WiFi connection settings
    WiFi_MAX_ATTEMPTS = 10
    
    # Bounds box for flight search (from secrets)
    BOUNDS_BOX = None
    
    @classmethod
    def initialize(cls):
        """Initialize configuration from secrets."""
        if 'bounds_box' not in secrets:
            raise ValueError("ERROR: 'bounds_box' not found in secrets.py!")
        
        cls.BOUNDS_BOX = secrets['bounds_box']
        
        # Build the full search URL
        cls.FR24_SEARCH_URL = cls.FR24_SEARCH_HEAD + cls.BOUNDS_BOX + cls.FR24_SEARCH_TAIL
        
        print("[CONFIG] Initialized with bounds:", cls.BOUNDS_BOX)
        return True
    
    @classmethod
    def get_color(cls, color_name):
        """Get a color by name. Returns None if not found."""
        return cls.COLORS.get(color_name)
    
    @classmethod
    def get_timing(cls, timing_name):
        """Get a timing value by name. Returns None if not found."""
        return cls.TIMINGS.get(timing_name)


# Initialize on module load
Config.initialize()
