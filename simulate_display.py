"""
FlightPortal - Terminal Display Simulator
Simulates the 64x32 LED matrix panel output in your terminal.
Run this on any PC - no hardware needed.

Usage:
    python simulate_display.py
    python simulate_display.py --demo       (cycle through all screens)
    python simulate_display.py --screen wifi_error
"""

import sys
import time
import os

DISPLAY_WIDTH = 64
DISPLAY_HEIGHT = 32

# ANSI color codes
class Color:
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    BLACK   = "\033[30m"
    RED     = "\033[31m"
    GREEN   = "\033[32m"
    YELLOW  = "\033[33m"
    BLUE    = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN    = "\033[36m"
    WHITE   = "\033[37m"
    BG_BLACK = "\033[40m"

    # Bright variants
    B_RED    = "\033[91m"
    B_GREEN  = "\033[92m"
    B_YELLOW = "\033[93m"
    B_BLUE   = "\033[94m"
    B_MAGENTA= "\033[95m"
    B_CYAN   = "\033[96m"
    B_WHITE  = "\033[97m"

    # Background
    BG_RED    = "\033[41m"
    BG_GREEN  = "\033[42m"
    BG_YELLOW = "\033[43m"


def clear():
    """Clear the terminal."""
    os.system('cls' if os.name == 'nt' else 'clear')


def rgb_hex_to_ansi(hex_color):
    """Map a 24-bit hex color to nearest ANSI terminal color."""
    r = (hex_color >> 16) & 0xFF
    g = (hex_color >> 8) & 0xFF
    b = hex_color & 0xFF

    # Dominant channel determines color
    if r > 200 and g < 100 and b < 100:
        return Color.B_RED
    elif r < 100 and g > 200 and b < 100:
        return Color.B_GREEN
    elif r > 200 and g > 150 and b < 100:
        return Color.B_YELLOW
    elif r > 200 and g < 100 and b > 150:
        return Color.B_MAGENTA
    elif r > 180 and g > 100 and b > 200:
        return Color.B_MAGENTA
    elif hex_color > 0xDD00DD:
        return Color.B_MAGENTA
    elif r < 100 and g < 100 and b > 150:
        return Color.B_BLUE
    elif r < 100 and g > 150 and b > 200:
        return Color.B_CYAN
    elif r > 200 and g > 100 and b < 50:
        return Color.B_YELLOW   # Orange
    else:
        return Color.B_WHITE


# ── Plane bitmap (12×12) same as real code ──────────────────────────────────
PLANE_PIXELS = set([
    (6,0),(6,1),(5,1),
    (4,2),(5,2),(6,2),
    (9,3),(5,3),(4,3),(3,3),
    (1,4),(2,4),(3,4),(4,4),(5,4),(6,4),(7,4),(8,4),(9,4),
    (1,5),(2,5),(3,5),(4,5),(5,5),(6,5),(7,5),(8,5),(9,5),
    (9,6),(5,6),(4,6),(3,6),
    (4,7),(5,7),(6,7),
    (5,8),(6,8),
    (6,9),
])


class FrameBuffer:
    """64x32 frame buffer that renders to terminal."""

    def __init__(self):
        # Pixels: (r, g, b) or None (off)
        self.buf = [[None] * DISPLAY_WIDTH for _ in range(DISPLAY_HEIGHT)]

    def clear(self):
        for y in range(DISPLAY_HEIGHT):
            for x in range(DISPLAY_WIDTH):
                self.buf[y][x] = None

    def set_pixel(self, x, y, color):
        if 0 <= x < DISPLAY_WIDTH and 0 <= y < DISPLAY_HEIGHT:
            self.buf[y][x] = color

    def draw_text(self, text, x, y, color, char_width=5):
        """Very small 5-pixel-wide bitmapped font (subset for demo)."""
        # Mini pixel font: each char is a list of column bitmasks (5 rows high)
        FONT = {
            ' ': [0x00, 0x00, 0x00],
            '-': [0x00, 0x04, 0x04, 0x04, 0x00],
            '/': [0x10, 0x08, 0x04, 0x02, 0x01],
            '0': [0x0E,0x11,0x11,0x11,0x0E],
            '1': [0x00,0x12,0x1F,0x10,0x00],
            '2': [0x12,0x19,0x15,0x15,0x12],
            '3': [0x11,0x15,0x15,0x15,0x0A],
            '4': [0x07,0x04,0x1F,0x04,0x04],
            '5': [0x17,0x15,0x15,0x15,0x09],
            '6': [0x0E,0x15,0x15,0x15,0x08],
            '7': [0x01,0x01,0x1D,0x03,0x01],
            '8': [0x0A,0x15,0x15,0x15,0x0A],
            '9': [0x02,0x15,0x15,0x0D,0x06],
            'A': [0x1E,0x05,0x05,0x05,0x1E],
            'B': [0x1F,0x15,0x15,0x15,0x0A],
            'C': [0x0E,0x11,0x11,0x11,0x0A],
            'D': [0x1F,0x11,0x11,0x11,0x0E],
            'E': [0x1F,0x15,0x15,0x11,0x11],
            'F': [0x1F,0x05,0x05,0x01,0x01],
            'G': [0x0E,0x11,0x15,0x15,0x1C],
            'H': [0x1F,0x04,0x04,0x04,0x1F],
            'I': [0x00,0x11,0x1F,0x11,0x00],
            'J': [0x08,0x10,0x10,0x10,0x0F],
            'K': [0x1F,0x04,0x0A,0x11,0x00],
            'L': [0x1F,0x10,0x10,0x10,0x10],
            'M': [0x1F,0x02,0x04,0x02,0x1F],
            'N': [0x1F,0x02,0x04,0x08,0x1F],
            'O': [0x0E,0x11,0x11,0x11,0x0E],
            'P': [0x1F,0x05,0x05,0x05,0x02],
            'Q': [0x0E,0x11,0x19,0x11,0x2E],
            'R': [0x1F,0x05,0x0D,0x15,0x12],
            'S': [0x12,0x15,0x15,0x15,0x09],
            'T': [0x01,0x01,0x1F,0x01,0x01],
            'U': [0x0F,0x10,0x10,0x10,0x0F],
            'V': [0x07,0x08,0x10,0x08,0x07],
            'W': [0x1F,0x10,0x08,0x10,0x1F],
            'X': [0x11,0x0A,0x04,0x0A,0x11],
            'Y': [0x03,0x04,0x18,0x04,0x03],
            'Z': [0x11,0x19,0x15,0x13,0x11],
        }

        cx = x
        for ch in text.upper():
            col_map = FONT.get(ch, FONT.get(' ', [0x00, 0x00, 0x00]))
            for col_idx, bits in enumerate(col_map):
                for row_bit in range(5):
                    if (bits >> row_bit) & 1:
                        self.set_pixel(cx + col_idx, y + row_bit, color)
            cx += len(col_map) + 1

    def draw_plane(self, x_offset, color):
        """Draw the plane bitmap at the given x offset."""
        for (px, py) in PLANE_PIXELS:
            self.set_pixel(x_offset + px, 10 + py, color)

    def render(self, title="LED Matrix Display (64x32)"):
        """Render the frame buffer to terminal."""
        # Top border
        print(f"\n  {Color.BOLD}┌{'─' * (DISPLAY_WIDTH * 2)}┐{Color.RESET}  {Color.B_WHITE}{title}{Color.RESET}")

        for y in range(DISPLAY_HEIGHT):
            line = f"  {Color.BOLD}│{Color.RESET}"
            for x in range(DISPLAY_WIDTH):
                color = self.buf[y][x]
                if color is None:
                    line += "  "  # off pixel = 2 spaces
                else:
                    ansi = rgb_hex_to_ansi(color)
                    line += f"{ansi}██{Color.RESET}"
            line += f"{Color.BOLD}│{Color.RESET}"
            print(line)

        print(f"  {Color.BOLD}└{'─' * (DISPLAY_WIDTH * 2)}┘{Color.RESET}")


# ── Screen builders ──────────────────────────────────────────────────────────

def screen_normal_flight(fb, flight_number, route, aircraft, airline=""):
    """Standard 3-row flight display."""
    fb.clear()
    fb.draw_text(flight_number, 1, 4,  0xEE82EE)   # Row 1: magenta - flight number
    fb.draw_text(route,        1, 15, 0x8B00FF)   # Row 2: indigo - route
    fb.draw_text(aircraft,     1, 25, 0xFFA500)   # Row 3: orange - aircraft


def screen_altitude_speed(fb, flight_number, route, alt_ft, speed_kts, aircraft):
    """Phase 2: Row 3 shows altitude + speed instead of aircraft."""
    fb.clear()
    fb.draw_text(flight_number,           1, 4,  0xEE82EE)
    fb.draw_text(route,                   1, 15, 0x8B00FF)
    fb.draw_text(f"{alt_ft}FT {speed_kts}KT", 1, 25, 0x00FF88)  # Phase 2: cyan-green


def screen_plane_animation(fb, plane_x, plane_color):
    """Plane animation frame."""
    fb.clear()
    fb.draw_plane(plane_x, plane_color)


def screen_wifi_error(fb):
    """Phase 2: WiFi error state."""
    fb.clear()
    fb.draw_text("WIFI",    4, 4,  0xFF0000)   # Red
    fb.draw_text("ERROR",   2, 14, 0xFF0000)
    fb.draw_text("CHECK",   2, 24, 0xFF4400)

    # Error indicator bar (top 2 rows red)
    for x in range(DISPLAY_WIDTH):
        fb.set_pixel(x, 0, 0xFF0000)
        fb.set_pixel(x, 1, 0xFF0000)


def screen_api_error(fb):
    """Phase 2: API error state."""
    fb.clear()
    fb.draw_text("FR24",   4, 4,  0xFFFF00)   # Yellow
    fb.draw_text("OFFLINE", 1, 14, 0xFFAA00)
    fb.draw_text("RETRY",  4, 24, 0xFFFF00)

    # Warning bars
    for x in range(DISPLAY_WIDTH):
        fb.set_pixel(x, 0, 0xFFAA00)
        fb.set_pixel(x, 1, 0xFFAA00)


def screen_no_flights(fb):
    """Display when sky is empty."""
    fb.clear()
    fb.draw_text("NO",      20, 8,  0x444444)
    fb.draw_text("FLIGHTS", 5, 18, 0x444444)


def screen_tail_logo(fb, flight_number, route, aircraft, airline_color):
    """Phase 2: Tailfin logo - plane colored per airline livery."""
    fb.clear()
    fb.draw_text(flight_number, 1, 4,  0xEE82EE)
    fb.draw_text(route,        1, 15, 0x8B00FF)
    fb.draw_text(aircraft,     1, 25, 0xFFA500)
    # Draw small airline color block (tail badge) top-right corner
    for y in range(0, 8):
        for x in range(DISPLAY_WIDTH - 10, DISPLAY_WIDTH - 2):
            fb.set_pixel(x, y, airline_color)


def screen_brightness_dim(fb, flight_number, route, aircraft, factor=0.3):
    """Phase 2: Dimmed display (night mode)."""
    fb.clear()
    # Apply dim factor to colors
    def dim(c): return int(c * factor)
    fb.draw_text(flight_number, 1, 4,  dim(0xEE82EE))
    fb.draw_text(route,        1, 15, dim(0x8B00FF))
    fb.draw_text(aircraft,     1, 25, dim(0xFFA500))


# ── Demo runner ──────────────────────────────────────────────────────────────

def print_legend():
    print(f"\n  {Color.B_WHITE}LEGEND:{Color.RESET}")
    print(f"  {Color.B_MAGENTA}██{Color.RESET} Row 1 - Flight Number (Violet)")
    print(f"  {Color.B_BLUE}██{Color.RESET}  Row 2 - Route (Indigo)")
    print(f"  {Color.B_YELLOW}██{Color.RESET} Row 3 - Aircraft or Alt/Speed (Orange/Cyan)")
    print(f"  {Color.B_RED}██{Color.RESET}  Error indicators")


def run_demo():
    fb = FrameBuffer()
    screens = [
        # (title, builder_fn, pause)
        ("SCREEN 1/7: Normal flight display (current behaviour)",
         lambda: screen_normal_flight(fb, "BA1234", "LHR-LAX", "B737"), 3),

        ("SCREEN 2/7: PHASE 2 — Altitude & Speed on Row 3",
         lambda: screen_altitude_speed(fb, "BA1234", "LHR-LAX", "28000", "420", "B737"), 3),

        ("SCREEN 3/7: PHASE 2 — Airline Tail Logo (British Airways blue)",
         lambda: screen_tail_logo(fb, "BA1234", "LHR-LAX", "B737", 0x0066CC), 3),

        ("SCREEN 4/7: PHASE 2 — Airline Tail Logo (Easyjet orange)",
         lambda: screen_tail_logo(fb, "EZY789", "LTN-BCN", "A320", 0xFF6600), 3),

        ("SCREEN 5/7: PHASE 2 — WiFi Error State (Red indicators)",
         lambda: screen_wifi_error(fb), 3),

        ("SCREEN 6/7: PHASE 2 — FR24 API Error (Yellow warning)",
         lambda: screen_api_error(fb), 3),

        ("SCREEN 7/7: PHASE 2 — Night Mode (Dimmed brightness)",
         lambda: screen_brightness_dim(fb, "BA1234", "LHR-LAX", "B737", factor=0.25), 3),
    ]

    print(f"\n{Color.BOLD}{Color.B_WHITE}FlightPortal Display Simulator{Color.RESET}")
    print(f"Cycling through {len(screens)} display screens...\n")
    print_legend()

    for title, builder, pause in screens:
        builder()
        fb.render(title)
        print(f"\n  {Color.B_WHITE}Next screen in {pause}s...{Color.RESET}", end="", flush=True)
        time.sleep(pause)
        clear()

    # Final: plane animation preview
    print(f"\n{Color.BOLD}Plane animation preview:{Color.RESET}")
    AIRLINE_COLORS = [0x0066CC, 0xFF6600, 0x4B0082, 0xFF0000]
    for cx in range(64, -15, -4):
        color = AIRLINE_COLORS[1]   # Orange EasyJet livery
        screen_plane_animation(fb, cx, color)
        fb.render("Plane animation (Phase 2: airline livery colour)")
        time.sleep(0.05)
        clear()

    print(f"\n{Color.B_GREEN}✓ Demo complete!{Color.RESET}\n")
    print_legend()
    print()


def run_single(screen_name):
    """Show a single named screen."""
    fb = FrameBuffer()
    screens = {
        'normal':      (lambda: screen_normal_flight(fb,    "BA1234", "LHR-LAX",  "B737"),           "Normal flight display"),
        'alt_speed':   (lambda: screen_altitude_speed(fb,   "BA1234", "LHR-LAX",  "28000", "420", "B737"), "Altitude & Speed (Phase 2)"),
        'tail_logo':   (lambda: screen_tail_logo(fb,        "BA1234", "LHR-LAX",  "B737", 0x0066CC), "Tail Logo (Phase 2)"),
        'wifi_error':  (lambda: screen_wifi_error(fb),                                                "WiFi Error (Phase 2)"),
        'api_error':   (lambda: screen_api_error(fb),                                                 "API Error (Phase 2)"),
        'no_flights':  (lambda: screen_no_flights(fb),                                                "No Flights"),
        'night_mode':  (lambda: screen_brightness_dim(fb,   "BA1234", "LHR-LAX",  "B737"),            "Night Mode Dim (Phase 2)"),
    }

    if screen_name not in screens:
        print(f"Unknown screen '{screen_name}'. Options: {', '.join(screens.keys())}")
        return

    fn, title = screens[screen_name]
    fn()
    fb.render(title)
    print_legend()
    print()


# ── Entry point ──────────────────────────────────────────────────────────────

if __name__ == '__main__':
    args = sys.argv[1:]

    if '--demo' in args:
        run_demo()
    elif '--screen' in args:
        idx = args.index('--screen')
        if idx + 1 < len(args):
            run_single(args[idx + 1])
        else:
            print("Usage: python simulate_display.py --screen <name>")
            print("Screens: normal, alt_speed, tail_logo, wifi_error, api_error, no_flights, night_mode")
    else:
        # Default: show all screens once without animation
        fb = FrameBuffer()
        print(f"\n{Color.BOLD}{Color.B_WHITE}FlightPortal Display Simulator{Color.RESET}")
        print(f"Usage: python simulate_display.py --demo   (animated)\n")
        print_legend()

        print(f"\n{Color.B_WHITE}--- CURRENT BEHAVIOUR ---{Color.RESET}")
        screen_normal_flight(fb, "BA1234", "LHR-LAX", "B737")
        fb.render("Normal: Flight No. | Route | Aircraft")

        print(f"\n{Color.B_CYAN}--- PHASE 2: ALTITUDE & SPEED ---{Color.RESET}")
        screen_altitude_speed(fb, "BA1234", "LHR-LAX", "28000", "420", "B737")
        fb.render("Phase 2: Flight No. | Route | Altitude + Speed")

        print(f"\n{Color.B_BLUE}--- PHASE 2: AIRLINE TAIL LOGO ---{Color.RESET}")
        screen_tail_logo(fb, "BA1234", "LHR-LAX", "B737", 0x0066CC)
        fb.render("Phase 2: Tail badge top-right (airline livery colour)")

        print(f"\n{Color.B_RED}--- PHASE 2: ERROR STATES ---{Color.RESET}")
        screen_wifi_error(fb)
        fb.render("Phase 2: WiFi Error State")

        screen_api_error(fb)
        fb.render("Phase 2: FR24 API Error State")

        print(f"\n{Color.B_YELLOW}--- PHASE 2: NIGHT MODE ---{Color.RESET}")
        screen_brightness_dim(fb, "BA1234", "LHR-LAX", "B737", factor=0.25)
        fb.render("Phase 2: Night Mode (30% brightness)")

        print()
