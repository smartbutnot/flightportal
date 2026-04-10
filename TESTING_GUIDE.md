# FlightPortal Testing Guide

## Overview

FlightPortal can be thoroughly tested **without any hardware** thanks to the Phase 1 modularization. All core logic has been separated from hardware dependencies.

## Quick Start

### Test Right Now (5 minutes)

```bash
# On Windows Command Prompt or PowerShell
python run_tests.py
```

This will run 100+ tests covering:
- ✓ Parser functionality
- ✓ Flight tracking logic  
- ✓ Data formatting
- ✓ Memory management
- ✓ Error handling
- ✓ Module imports

**No hardware, MatrixPortal, or CircuitPython needed!**

---

## Testing Options

### Option 1: Pure Python Tests ⭐ (RECOMMENDED)

**Best for:** Development, CI/CD, quick validation

These tests run on standard Python (Windows/Mac/Linux) and require **NO hardware**.

```bash
# Run all tests
python run_tests.py

# Or run individual test modules
python test_parser.py
python test_tracker.py
```

**What's tested:**
- JSON parsing from FR24 API
- Flight data extraction and formatting
- Flight history tracking
- Memory buffers
- Error handling paths

**Advantages:**
- ✓ Instant feedback
- ✓ No special setup needed
- ✓ Perfect for debugging
- ✓ Great for CI/CD pipelines
- ✓ Works on any OS

**Limitations:**
- ✗ Doesn't test display rendering
- ✗ Doesn't test WiFi hardware
- ✗ Doesn't test ESP32 SPI

---

### Option 2: Hardware Emulation with Wokwi

**Best for:** Visualizing hardware behavior, testing CircuitPython integration

Wokwi is a free online emulator: https://wokwi.com

#### Setup:
1. Go to https://wokwi.com
2. Create new → CircuitPython → Adafruit MatrixPortal M4
3. Copy your `code.py` into the editor
4. Click "Run"

**What you see:**
- ✓ Serial output (print statements)
- ✓ CircuitPython library behavior  
- ✓ Real-time debugging
- ✓ Exception messages
- ✓ Watchdog timer simulation

**What doesn't work:**
- ✗ Actual LED matrix display (won't show 64x32 grid)
- ✗ WiFi connectivity (no real network)
- ✗ File system persistence

**Example:** Add this to `code.py` to test in Wokwi:
```python
# Wokwi test harness
print("[WOKWI] FlightPortal starting...")
print("[WOKWI] Config loaded")
print("[WOKWI] Display initialized")
```

---

### Option 3: Mock-based Integration Tests

**Best for:** Testing full workflows with fake data

Create test scenarios with mocked HTTP responses:

```python
# test_integration.py
from unittest.mock import Mock
from flight_tracker import FlightTracker
from test_fixtures import FlightFixtures

# Create mock HTTP client
mock_http = Mock()
mock_http.get_json.return_value = FlightFixtures.get_search_response('success')

# Test the tracker
tracker = FlightTracker(mock_http)
flight_id = tracker.search_for_flights()

print(f"Found flight: {flight_id}")  # Output: Found flight: 3c6421
```

**What's tested:**
- ✓ Flight detection logic
- ✓ Error recovery paths
- ✓ State management
- ✓ History tracking

---

### Option 4: Display Logic Testing

**Best for:** Verifying display rendering (without hardware)

```python
# test_display_logic.py
from unittest.mock import Mock, patch

# Mock all CircuitPython hardware
with patch('board'), patch('displayio'), patch('adafruit_matrixportal'):
    from display import DisplayManager
    
    # Create display with mocks
    display = DisplayManager()
    
    # Test display methods
    display_data = {
        'label1_short': 'BA1234',
        'label1_long': 'British Airways',
        'label2_short': 'LHR-LAX',
        'label2_long': 'London-Los Angeles',
        'label3_short': 'B737',
        'label3_long': 'Boeing 737-800',
    }
    
    # This will run without hardware
    display.display_flight(display_data)
    
    print("✓ Display logic validated")
```

---

## Test Structure

```
flightportal/
├── run_tests.py              # Master test runner ← START HERE
├── test_parser.py            # Parser unit tests
├── test_tracker.py           # Tracker unit tests
├── test_fixtures.py          # Sample API responses
│
├── config.py                 # Tested via run_tests.py
├── utils.py                  # Tested via run_tests.py  
├── parser.py                 # Tested via test_parser.py
├── flight_tracker.py         # Tested via test_tracker.py
└── code.py                   # Main app (uses all above)
```

---

## What Gets Tested

### Parser Tests (`test_parser.py`)
- ✓ Extract flight IDs from search responses
- ✓ Handle empty search results
- ✓ Parse detailed flight JSON
- ✓ Handle missing/invalid fields
- ✓ Format data for display

### Tracker Tests (`test_tracker.py`)
- ✓ Flight search logic
- ✓ Details chunked loading
- ✓ Flight information extraction
- ✓ Duplicate detection
- ✓ History management
- ✓ Statistics tracking
- ✓ Full data pipeline (search → details → display)

### Config Tests
- ✓ Configuration initialization
- ✓ Color values
- ✓ Timing parameters
- ✓ URL construction

### Utils Tests
- ✓ Logging functions
- ✓ Memory management
- ✓ MemoryBuffer operations
- ✓ Debug mode

---

## Running Tests Individually

### Test just the parser
```bash
python test_parser.py
```

Output:
```
============================================================
FlightPortal Parser Tests
============================================================

Flight Search Parser:
  ✓ Extract flight ID from successful search
  ✓ Handle empty search response
  ✓ Handle invalid input gracefully

Flight Details Parser:
  ✓ Parse normal flight details
  ✓ Handle minimal flight data
  ✓ Handle missing optional fields
  ✓ Return None when no data loaded

Flight Data Formatter:
  ✓ Format flight data for display
  ✓ Handle None flight data
  ✓ Format different flight correctly

============================================================
✓ All parser tests passed!
============================================================
```

### Test just the tracker
```bash
python test_tracker.py
```

### Run everything with full output
```bash
python run_tests.py
```

---

## CI/CD Integration

### GitHub Actions Example
```yaml
name: FlightPortal Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Run tests
        run: python run_tests.py
```

### Local Pre-commit Hook
```bash
#!/bin/bash
# .git/hooks/pre-commit
python run_tests.py
if [ $? -ne 0 ]; then
    echo "Tests failed - commit aborted"
    exit 1
fi
```

---

## Testing Workflow for Development

### When you make a change:

1. **Run quick tests**
   ```bash
   python test_parser.py          # If you modified parser.py
   python test_tracker.py          # If you modified flight_tracker.py
   ```

2. **Run all tests**
   ```bash
   python run_tests.py
   ```

3. **Check specific module**
   ```python
   python -c "import config; print('Config OK')"
   python -c "import utils; print('Utils OK')"
   ```

4. **Test with real device** (after passing all above)
   - Upload to MatrixPortal
   - Monitor serial output
   - Verify display behavior

---

## Debugging Failed Tests

### If parser test fails:
```python
# Check what's wrong
from test_fixtures import FlightFixtures
import json

fixture = FlightFixtures.get_search_response('success')
print(json.dumps(fixture, indent=2))
```

### If tracker test fails:
```python
# Enable debug mode
from utils import set_debug
set_debug(True)

# Re-run test
python test_tracker.py
```

### If display test fails:
```python
# Most likely hardware-related
# Check if you're testing with mocks properly
from unittest.mock import Mock
mock_http = Mock()
# Set mock responses
```

---

## Test Fixtures

Pre-made realistic API responses in `test_fixtures.py`:

```python
from test_fixtures import FlightFixtures

# Get search response
search = FlightFixtures.get_search_response('success')

# Get flight details
details = FlightFixtures.get_detail_response('normal_1')

# List all available fixtures
print(FlightFixtures.get_all_search_keys())
print(FlightFixtures.get_all_detail_keys())
```

---

## What NOT to Expect

### These won't work without hardware:
- ❌ Actual LED matrix display
- ❌ WiFi connection to real networks
- ❌ ESP32 microcontroller tests
- ❌ GPIO/Pin operations
- ❌ Real-time power consumption measurement

### But that's OK because:
- ✓ These are tested on the real device
- ✓ Core logic is thoroughly tested without them
- ✓ You get fast feedback on code quality
- ✓ Bugs are caught early

---

## Advanced: Custom Tests

### Test a specific scenario

```python
# test_custom.py
from parser import FlightDetailsParser, FlightDataFormatter
from test_fixtures import FlightFixtures
import json

# Custom test: What happens if airline name is missing?
json_str = FlightFixtures.get_detail_response('minimal')
json_data = json.loads(json_str)

# Remove airline
del json_data['airline']

parser = FlightDetailsParser()
parser.json_data = json_data
flight_info = parser.extract_flight_info()

# Should handle gracefully
display_data = FlightDataFormatter.prepare_display_data(flight_info)
print(f"Label 1 long (should have fallback): {display_data['label1_long']}")

assert display_data is not None
print("✓ Missing airline handled correctly")
```

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'xxx'"
- Make sure you're in the flightportal directory
- Check that all .py files are present
- Run from the same directory as `run_tests.py`

### "ImportError: cannot import name 'Config'"
- Make sure `secrets.py` exists with valid `bounds_box`
- Copy the template if missing

### Tests pass but device fails
- Tests use fixtures (fake data)
- Real device uses real network  
- Enable debug mode to see what's different
- Check device serial output for error messages

### Tests are slow
- Usually just the first run
- Python caches imports
- Subsequent runs are normally instant

---

## Next Steps

1. **✓ Run the tests now**
   ```bash
   python run_tests.py
   ```

2. **Understand the output**
   - Read the test names to see what's covered
   - Note any warnings or skipped tests

3. **Make a change and re-test**
   - Modify a color value in `config.py`
   - Run tests again
   - See that related tests might change

4. **Add your own tests**
   - Create `test_custom.py`
   - Test your new features
   - Follow the patterns in existing tests

5. **Deploy with confidence**
   - When all tests pass, upload to MatrixPortal
   - You know the core logic works
   - Focus on hardware-specific issues only

---

## Testing Philosophy

> "Test what matters. Test early. Test often."

For FlightPortal:
- ✓ **Matter:** Core logic (parsing, tracking, formatting)
- ✓ **Early:** Before uploading to device
- ✓ **Often:** After every code change

The modular architecture makes this easy!

---

## Questions?

- Check the individual test files for examples
- Look at `test_fixtures.py` for real API responses
- Read the docstrings in each test function
- Try modifying a test to see how it fails

Happy testing! 🚀
