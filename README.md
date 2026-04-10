# flightportal
Project for displaying the details of planes overhead on an Adafruit MatrixPortal and LED matrix

(video sped up to make the file fit, the speeds and delays are configurable anyway)

https://user-images.githubusercontent.com/103124527/206902629-1f31bd41-d8a8-415e-a35a-625efb20b3d6.MOV

Uses an Adafruit MatrixPortal and a 64x32 LED/RGB Matrix (P4), and some fairly hacked-together FlightRadar24 API-style scraping to display the details of flights passing overhead. That code being unoffical, it may break at any time!

To make one you will need:

1. A MatrixPortal (https://www.adafruit.com/product/4745)
2. A P4, 64x32 RGB matrix panel (I get mine from Aliexpress)
3. The case I designed (https://www.thingiverse.com/thing:5701517)
4. An adafruit acrylic diffuser (https://www.adafruit.com/product/4749) - available various places
5. 6 M3 screws (sorry, said M5 before but was looking at the wrong ones, my bad. Think mine are 8mm long, little bit more would be OK, shorter probably a problem)
6. Optional: Uglu dashes to stick the diffuser on, the case holds mine on pretty well though (https://www.protapes.com/products/uglu-600-dashes-sheets)

Prep the portal as detailed here (https://learn.adafruit.com/adafruit-matrixportal-m4/prep-the-matrixportal), put the code and secrets files on, put your wifi details and the geo box you want to search in the secrets file, and you should be good to go!

If you'd like to change the layout, colours or the flight info displayed, all that is pretty configurable, have a look at code.py. Hopefully the comments are fairly self explanatory if you're happy hacking around with python.

The libaries it needs are I think all part of the recommended prep above, but for info they are:

- adafruit_fakerequests
- adafruit_requests
- adafruit_bitmap_font
- adafruit_io
- adafruit_matrixportal
- adafruit_minimqtt
- adafruit_display_text
- adafruit_portalbase

For power, the easiest thing is to use the cable that came with your matrix panel, as long as it has two prongs that go to the screws on the matrixportal. All that's needed is for the portal to connect to the power port on the panel - we're not using much power here (I clock it at about 2w). Any decent usb power supply connected to the portal should do it.

![IMG-2179](https://user-images.githubusercontent.com/103124527/208709167-dd4b6ff2-4c80-4e38-840f-e5b958e2ed78.jpg)

I soldered a connection straight onto the panel's power port as below, for neatness, but that's completely optional. 

![IMG_2125](https://user-images.githubusercontent.com/103124527/206903066-7af5c076-101e-4598-b3ba-0f64766e4162.jpg)
![IMG_2126_small](https://user-images.githubusercontent.com/103124527/206903084-42378ce0-b8d8-4810-a18a-f35b9a509752.jpg)
![IMG_2127_small](https://user-images.githubusercontent.com/103124527/206903089-16d0f7f7-2dc0-4082-a012-0e1c9999a63a.jpg)
![IMG_2128_small](https://user-images.githubusercontent.com/103124527/206903092-0a131b80-cd20-4c8c-b892-9b0a5c1d544b.jpg)

For debugging, use putty or similar, see what COM port the portal is on (device manager in windows will show you), and run a serial connection to that port at 115200. It should print out helpful messages about errors, flights it sees, etc. You can also paste the URLs you see in the code into a browser and check you can find flights, etc.

---

## Software Modernisation (2026)

The project has been significantly refactored and extended from the original single-file design. All original hardware behaviour is preserved.

### Architecture — Modular Refactor (Phase 1)

`code.py` was split into focused modules so each concern can be maintained, patched, and tested independently:

| File | Responsibility |
|---|---|
| `code.py` | Application entry point and main loop |
| `config.py` | All colours, timings, URLs, and feature flags in one place |
| `network.py` | WiFi connection management and HTTP client with retry logic |
| `parser.py` | Defensive FR24 JSON parsing — tolerant of API schema changes |
| `display.py` | Matrix display rendering, animations, and error states |
| `flight_tracker.py` | Flight detection, deduplication, and history tracking |
| `utils.py` | Logging, memory management, and pre-allocated byte buffers |
| `test_fixtures.py` | Sample FR24 API responses for offline testing |

### New Features (Phase 2)

**Altitude & Speed on Row 3**
Row 3 now shows live altitude (ft) and speed (kts) extracted from the FR24 trail data — data already fetched as part of the existing request, no extra network calls.
Toggle back to aircraft code/model by setting `Config.ROW3_MODE = 'aircraft'` in `config.py`.

**Airline Tail Logo Colour**
The plane animation uses the airline's livery colour instead of a fixed indigo.
17 airlines are pre-mapped (British Airways, EasyJet, Ryanair, Lufthansa, KLM, Emirates, and more).
Add more entries in `Config.AIRLINE_COLORS` in `config.py` using the IATA flight number prefix.

**Error State Display**
WiFi failures show `WiFi ERROR / Reconnecting` in red on the matrix.
FR24 API failures show `FR24 OFFLINE / Retrying...` in orange.
Label colours restore automatically when a flight is found again.

**Brightness Auto-Adjust**
Display brightness follows a configurable 24-hour schedule so it dims at night.
Default schedule in `config.py`:

```
 midnight – 6am   10%
 6am – 8am        30%
 8am – 8pm       100%  (full brightness)
 8pm – 10pm       50%
 10pm – midnight  20%
```

Disable entirely with `Config.BRIGHTNESS_ENABLED = False`.

---

## Development & Testing

All core logic can be tested on any Windows/Mac/Linux machine — no MatrixPortal hardware required.

### Run the full test suite

```bash
python run_tests.py
```

Runs 50+ tests covering parsing, flight tracking, memory management, configuration, and error handling. Completes in under 1 second.

### Run individual test modules

```bash
python test_parser.py       # FR24 JSON parsing and display formatting
python test_tracker.py      # Flight detection, deduplication, history
```

### Preview the display in your terminal

Simulates the 64×32 LED matrix panel output using ANSI colours.

```bash
# Show all screens at once
python simulate_display.py

# Animated walkthrough (3 seconds per screen + plane animation)
python simulate_display.py --demo

# Show a single named screen
python simulate_display.py --screen normal
python simulate_display.py --screen alt_speed
python simulate_display.py --screen tail_logo
python simulate_display.py --screen wifi_error
python simulate_display.py --screen api_error
python simulate_display.py --screen night_mode
python simulate_display.py --screen no_flights
```

### Enable verbose debug logging

Set the flag at runtime or add `set_debug(True)` at the top of `code.py`:

```python
from utils import set_debug
set_debug(True)
```

All modules then print `[DEBUG]` lines for every network call, JSON parse step, and display update.

### Configuration quick-reference

All user-adjustable settings are in `config.py`. Key options:

| Setting | Default | Effect |
|---|---|---|
| `ROW3_MODE` | `'alt_speed'` | `'alt_speed'` for altitude/speed, `'aircraft'` for model |
| `BRIGHTNESS_ENABLED` | `True` | Set `False` for always-full brightness |
| `BRIGHTNESS_SCHEDULE` | See above | List of `(start_hour, end_hour, brightness)` tuples |
| `AIRLINE_COLORS` | 17 airlines | Add entries as `'PREFIX': 0xRRGGBB` |
| `QUERY_DELAY` | `30` | Seconds between FR24 searches |
| `TIMINGS['text_scroll_speed']` | `0.04` | Seconds per pixel for text scrolling |
| `TIMINGS['plane_animation_speed']` | `0.04` | Seconds per pixel for plane animation |
