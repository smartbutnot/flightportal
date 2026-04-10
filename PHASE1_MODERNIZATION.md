# FlightPortal - Phase 1 Modularization

## Overview

Phase 1 refactoring successfully separated FlightPortal's monolithic `code.py` into modular, testable components. This enables easier maintenance, testing, feature development, and dependency patching.

## New Architecture

### Module Structure

```
flightportal/
├── code.py                  # Main entry point & application controller
├── config.py               # Configuration management (centralized settings)
├── network.py              # WiFi & HTTP client with error handling
├── parser.py               # Defensive FR24 JSON parsing
├── display.py              # Matrix display rendering & animations
├── flight_tracker.py       # Core flight detection & tracking logic
├── utils.py                # Helper utilities (logging, memory, buffers)
├── test_fixtures.py        # Sample API responses for testing
├── secrets.py              # User credentials (unchanged)
└── README.md               # Original documentation
```

### Module Responsibilities

#### `config.py`
- **Purpose:** Centralized configuration and constants
- **Key Classes:**
  - `Config`: Central settings class with:
    - Color palette definitions
    - Animation/timing parameters
    - API URLs and endpoints
    - HTTP headers
    - Memory buffer sizes
    - WiFi settings
- **Benefits:** Easy to adjust timings, colors, or API settings without modifying core logic

#### `utils.py`
- **Purpose:** Shared utility functions and helpers
- **Key Classes:**
  - `MemoryBuffer`: Pre-allocated fixed-size byte buffer for memory-constrained devices
- **Key Functions:**
  - Logging (debug, info, warning, error)
  - Memory management (gc, stats)
  - Debug mode control
- **Benefits:** Cleaner logging, reusable memory utilities

#### `network.py`
- **Purpose:** Network connectivity and HTTP communication
- **Key Classes:**
  - `WiFiManager`: Handle WiFi connections with auto-reconnect
  - `HTTPClient`: Safe HTTP requests with error handling
- **Benefits:**
  - Robust WiFi reconnection logic
  - Centralized error handling
  - Easy to test with mock objects
  - Supports chunked downloads

#### `parser.py`
- **Purpose:** Defensive JSON parsing with safety checks
- **Key Classes:**
  - `FlightSearchParser`: Extract flight IDs from search responses
  - `FlightDetailsParser`: Parse detailed flight information
  - `FlightDataFormatter`: Format parsed data for display
- **Benefits:**
  - Tolerant of API schema changes
  - Clear separation of parsing concerns
  - Reusable with test fixtures
  - Better error messages

#### `display.py`
- **Purpose:** Matrix panel display management
- **Key Classes:**
  - `PlaneGraphic`: Plane bitmap and animation
  - `DisplayManager`: Display lifecycle and rendering
- **Key Methods:**
  - `set_label()`: Update text
  - `clear_all_labels()`: Clear display
  - `animate_plane()`: Plane animation
  - `scroll_label()`: Text scrolling
  - `display_flight()`: Full flight display sequence
  - `show_error()`: Error state display
- **Benefits:**
  - Display logic isolated from core logic
  - Easy to add new display modes
  - Testing without hardware

#### `flight_tracker.py`
- **Purpose:** Core flight detection and state management
- **Key Class:**
  - `FlightTracker`: Main flight tracking logic
- **Key Methods:**
  - `search_for_flights()`: Query FR24 API
  - `fetch_flight_details()`: Get detailed flight info
  - `process_new_flight()`: Handle new detections
  - `get_history()`: Flight tracking history
  - `get_stats()`: Tracking statistics
- **Benefits:**
  - Testable flight logic
  - Flight history tracking for Phase 2 features
  - Clean API for main loop

#### `code.py`
- **Purpose:** Application entry point and main loop
- **Key Class:**
  - `FlightPortalApp`: Application controller
- **Key Methods:**
  - `startup()`: Initialize subsystems
  - `run_once()`: Single iteration of main loop
  - `run()`: Main event loop
- **Benefits:**
  - Very readable main logic
  - Easy to understand application flow
  - Centralized error handling

## Key Improvements

### 1. Defensive JSON Parsing
- Handle missing fields gracefully
- Better error messages
- Resilient to API changes

### 2. Memory Management
- `MemoryBuffer` class for pre-allocated buffers
- Explicit garbage collection points
- Memory status monitoring

### 3. Error Handling
- Structured logging (debug, info, warning, error)
- Error display on matrix
- WiFi reconnect logic

### 4. Testability
- No global mutable state
- Dependency injection (HTTP client passed to tracker)
- Test fixtures with sample data
- Can be tested without hardware

### 5. Configuration
- Centralized config class
- Easy to tweak without code changes
- Clear documentation of each setting

### 6. Separation of Concerns
- Network layer separate from business logic
- Display rendering separate from flight tracking
- Parser logic separate from data fetching

## Usage

### Running the Application
```python
# Same as before - just run code.py
# It will import all modules and start the FlightPortalApp
```

### Development / Testing
```python
# Test parser with fixtures
from test_fixtures import FlightFixtures
from parser import FlightSearchParser

fixture = FlightFixtures.get_search_response('success')
parser = FlightSearchParser()
flight_id = parser.extract_flight_id(fixture)

# Test flight tracking (mock HTTP)
from flight_tracker import FlightTracker
from unittest.mock import Mock

mock_http = Mock()
tracker = FlightTracker(mock_http)
# Set mock responses and test logic

# Enable debug logging
from utils import set_debug
set_debug(True)
```

## Migration Notes

### What Changed
- Original `code.py` functionality is preserved
- All imports are internal (modules import each other)
- No external dependencies added

### What Stayed the Same
- Hardware interface remains unchanged
- API endpoints unchanged
- Display logic and animations unchanged
- Configuration via `secrets.py`

### Breaking Changes
- None. Original `secrets.py` format still works.

## Next Steps (Phase 2)

### Short Term (Ready Now)
1. Error state display (visual WiFi/API feedback)
2. Flight history statistics
3. Altitude/speed data extraction (already in JSON)
4. Multiple search zones

### Medium Term (Future)
1. Web dashboard for configuration
2. Local caching of flights
3. Brightness auto-adjust
4. Extended flight information display

### Long Term
1. Home automation webhooks
2. Flight database with analytics
3. Machine learning for flight filtering

## Testing Strategy

### Unit Tests (Create Later)
- `test_parser.py`: Test JSON parsing with fixtures
- `test_config.py`: Test configuration loading
- `test_display.py`: Test display methods

### Integration Tests (Create Later)
- Mock HTTP responses
- Test full flight processing pipeline
- Test WiFi reconnect behavior

### Manual Testing
- Enable debug mode: `utils.set_debug(True)`
- Monitor serial output for detailed logging
- Use test fixtures to validate parsing

## Debugging

### Enable Debug Logging
Set `DEBUG_MODE = True` in `utils.py` or call:
```python
from utils import set_debug
set_debug(True)
```

### Memory Status
Check at startup and periodically:
```python
from utils import print_memory_status
print_memory_status()
```

### View Module Usage
```python
# See how modules interact
import config
import network
import parser
import display
import flight_tracker

# All can be imported independently for testing
```

## Dependencies

### Hardware
- MatrixPortal M4
- ESP32 WiFi co-processor
- 64x32 RGB LED matrix panel

### Software (unchanged)
- adafruit_matrixportal
- adafruit_requests
- adafruit_esp32spi
- adafruit_display_text

### CircuitPython
- Tested with version 8.x (verify your version matches)
- See README.md for full setup instructions

## Architecture Diagram

```
┌─────────────────────┐
│  code.py (Main)     │
│ FlightPortalApp     │
└──────────┬──────────┘
           │
    ┌──────┼──────┐
    │      │      │
    ▼      ▼      ▼
┌────────┐ ┌──────────┐  ┌──────────────┐
│display │ │  flight_ │  │   network    │
│        │ │ tracker  │  │              │
└────────┘ └────┬─────┘  └──────┬───────┘
                │               │
                ▼               ▼
          ┌─────────────┐  ┌──────────┐
          │  parser.py  │  │config.py │
          └─────────────┘  └──────────┘
                │               │
                └───────┬───────┘
                        ▼
                  ┌──────────┐
                  │utils.py  │
                  └──────────┘
```

## Code Review Checklist for Future Changes

- [ ] All global state eliminated? (None should remain)
- [ ] New code follows module organization?
- [ ] Error handling includes logging?
- [ ] Watchdog feeding maintained?
- [ ] Memory usage considered?
- [ ] Defensive parsing for external APIs?
- [ ] Configuration moved to config.py?
- [ ] Module imports self-documenting?

## Conclusion

Phase 1 transforms FlightPortal from a monolithic script into a maintainable, testable system. The codebase is now ready for:

1. **Dependency patching** - Easy to update individual modules
2. **Feature development** - Clear module contracts
3. **Bug fixes** - Isolated, testable components
4. **Hardware updates** - Modular hardware abstraction ready
5. **Testing** - No global state means testable code

The architecture supports Phase 2 enhancements while maintaining full backward compatibility.
