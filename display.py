"""
Display management for FlightPortal matrix panel.
Handles rendering, animations, and text scrolling.
"""

import time
import board
import terminalio
import displayio
import adafruit_display_text.label
from adafruit_matrixportal.matrixportal import MatrixPortal
from microcontroller import watchdog as w

from config import Config
from utils import log_info, log_warning, debug_print


def _get_brightness_for_hour(hour):
    """Phase 2: Return brightness (0.0-1.0) for the given 24h hour."""
    if not Config.BRIGHTNESS_ENABLED:
        return 1.0
    for start, end, brightness in Config.BRIGHTNESS_SCHEDULE:
        if start <= hour < end:
            return brightness
    return Config.BRIGHTNESS_DEFAULT


class PlaneGraphic:
    """Manage the plane bitmap and animation."""
    
    def __init__(self):
        """Create and initialize the plane bitmap."""
        # Create 12x12 bitmap for plane
        self.bitmap = displayio.Bitmap(12, 12, 2)
        self.palette = displayio.Palette(2)
        self.palette[1] = Config.DEFAULT_PLANE_COLOR
        self.palette[0] = 0x000000  # Black background

    def set_color(self, color):
        """Phase 2: Change plane color (used for airline tail logo)."""
        self.palette[1] = color
        debug_print(f"Plane color set to: {hex(color)}")
        
        # Draw plane shape using pixel coordinates
        # (This is the same pattern as original code.py)
        self.bitmap[6, 0] = self.bitmap[6, 1] = self.bitmap[5, 1] = 1
        self.bitmap[4, 2] = self.bitmap[5, 2] = self.bitmap[6, 2] = 1
        self.bitmap[9, 3] = self.bitmap[5, 3] = self.bitmap[4, 3] = self.bitmap[3, 3] = 1
        self.bitmap[1, 4] = self.bitmap[2, 4] = self.bitmap[3, 4] = self.bitmap[4, 4] = 1
        self.bitmap[5, 4] = self.bitmap[6, 4] = self.bitmap[7, 4] = self.bitmap[8, 4] = 1
        self.bitmap[9, 4] = 1
        self.bitmap[1, 5] = self.bitmap[2, 5] = self.bitmap[3, 5] = self.bitmap[4, 5] = 1
        self.bitmap[5, 5] = self.bitmap[6, 5] = self.bitmap[7, 5] = self.bitmap[8, 5] = 1
        self.bitmap[9, 5] = 1
        self.bitmap[9, 6] = self.bitmap[5, 6] = self.bitmap[4, 6] = self.bitmap[3, 6] = 1
        self.bitmap[6, 9] = self.bitmap[6, 8] = self.bitmap[5, 8] = 1
        self.bitmap[4, 7] = self.bitmap[5, 7] = self.bitmap[6, 7] = 1
        
        self.tile_grid = displayio.TileGrid(self.bitmap, pixel_shader=self.palette)
        self.group = displayio.Group()
        self.group.append(self.tile_grid)
        
        log_info("Plane graphic initialized")
    
    def get_group(self):
        """Return the display group for the plane."""
        return self.group


class DisplayManager:
    """Manage the matrix portal display and text rendering."""
    
    def __init__(self):
        """Initialize the matrix portal and display components."""
        # Create MatrixPortal instance
        self.portal = MatrixPortal(
            headers=Config.HTTP_HEADERS,
            rotation=Config.DISPLAY_ROTATION,
            debug=Config.DISPLAY_DEBUG
        )
        
        # Get the ESP from portal for WiFi (will be set up separately)
        self.esp = None
        
        self.display = self.portal.display
        self.width = self.display.width
        self.height = self.display.height

        # Phase 2: apply brightness schedule on startup
        self._apply_brightness()

        # Create plane graphic
        self.plane = PlaneGraphic()

        # Create three text labels
        self.labels = {}
        self.label_colors = [
            Config.get_color('row_one'),
            Config.get_color('row_two'),
            Config.get_color('row_three'),
        ]
        self._create_labels()

        # Current display group showing text
        self.text_group = displayio.Group()
        self._add_labels_to_group()
        self.display.show(self.text_group)

        log_info(f"Display initialized: {self.width}x{self.height}")

    def _apply_brightness(self):
        """Phase 2: Set display brightness according to time schedule."""
        try:
            import rtc
            hour = rtc.RTC().datetime.tm_hour
            brightness = _get_brightness_for_hour(hour)
            self.display.brightness = brightness
            log_info(f"Brightness set to {brightness:.0%} for hour {hour}")
        except Exception:
            # RTC not available or time not set - use default
            self.display.brightness = Config.BRIGHTNESS_DEFAULT
            debug_print("RTC unavailable, using default brightness")
    
    def _create_labels(self):
        """Create the three text labels."""
        colors = [
            Config.get_color('row_one'),
            Config.get_color('row_two'),
            Config.get_color('row_three'),
        ]
        
        positions = [(1, 4), (1, 15), (1, 25)]
        
        for i in range(3):
            label = adafruit_display_text.label.Label(
                terminalio.FONT,
                color=colors[i],
                text=""
            )
            label.x, label.y = positions[i]
            self.labels[f'label{i+1}'] = label
        
        log_info("Text labels created")
    
    def _add_labels_to_group(self):
        """Add all labels to the text group."""
        for label in self.labels.values():
            self.text_group.append(label)
    
    def set_label(self, label_num, text):
        """Set text for a specific label (1, 2, or 3)."""
        label_key = f'label{label_num}'
        if label_key in self.labels:
            self.labels[label_key].text = str(text)
            debug_print(f"Label {label_num} set to: {text}")
    
    def clear_all_labels(self):
        """Clear all text labels."""
        for label_num in range(1, 4):
            self.set_label(label_num, "")
        debug_print("All labels cleared")
    
    def animate_plane(self, plane_color=None):
        """Phase 2: Animate the plane with optional airline livery color."""
        timing = Config.get_timing('plane_animation_speed')

        # Apply airline tail logo color if provided
        if plane_color is not None:
            self.plane.set_color(plane_color)
        else:
            self.plane.set_color(Config.DEFAULT_PLANE_COLOR)

        self.display.show(self.plane.get_group())

        for x in range(self.width + 24, -12, -1):
            self.plane.group.x = x
            w.feed()
            time.sleep(timing)

        log_info("Plane animation complete")
    
    def scroll_label(self, label_num):
        """Scroll a label from right to left."""
        label_key = f'label{label_num}'
        if label_key not in self.labels:
            return
        
        label = self.labels[label_key]
        timing = Config.get_timing('text_scroll_speed')
        
        label.x = self.width
        
        # Get bounding box to know when label is fully scrolled
        bbox = label.bounding_box
        right_edge_offset = bbox[2] if len(bbox) > 2 else 0
        
        for x in range(self.width + 1, -right_edge_offset, -1):
            label.x = x
            w.feed()
            time.sleep(timing)
    
    def display_flight(self, display_data):
        """
        Show flight information with animation.
        Phase 2: refreshes brightness, uses airline plane color.
        """
        if not display_data:
            self.clear_all_labels()
            return

        # Phase 2: Refresh brightness every time a new flight displays
        self._apply_brightness()

        timing_pause = Config.get_timing('pause_between_scrolls')

        self.display.show(self.text_group)

        # Set short labels
        self.set_label(1, display_data.get('label1_short', ''))
        self.set_label(2, display_data.get('label2_short', ''))
        self.set_label(3, display_data.get('label3_short', ''))
        time.sleep(timing_pause)

        # Scroll each label with long text
        for label_num in range(1, 4):
            long_key = f'label{label_num}_long'
            short_key = f'label{label_num}_short'

            if long_key in display_data and display_data[long_key]:
                self.set_label(label_num, display_data[long_key])
                self.scroll_label(label_num)
                self.set_label(label_num, display_data.get(short_key, ''))
                time.sleep(timing_pause)

        log_info("Flight display complete")
    
    def show_error(self, error_type):
        """
        Phase 2: Display a visual error state with colored labels.
        error_type: 'wifi' | 'api' | 'memory'
        """
        self.display.show(self.text_group)
        self.clear_all_labels()

        if error_type == 'wifi':
            # Change row 1 label to red
            self.labels['label1'].color = Config.get_color('error_wifi')
            self.labels['label2'].color = Config.get_color('error_wifi')
            self.set_label(1, "WiFi ERROR")
            self.set_label(2, "Reconnecting")
            self.set_label(3, "")
        elif error_type == 'api':
            self.labels['label1'].color = Config.get_color('error_api')
            self.labels['label2'].color = Config.get_color('error_api')
            self.set_label(1, "FR24 OFFLINE")
            self.set_label(2, "Retrying...")
            self.set_label(3, "")
        elif error_type == 'memory':
            self.labels['label1'].color = Config.get_color('error_wifi')
            self.set_label(1, "Low Memory")
            self.set_label(2, "Restarting")
        else:
            self.labels['label1'].color = Config.get_color('error_wifi')
            self.set_label(1, "ERROR")

        log_info(f"Showing error: {error_type}")

    def restore_label_colors(self):
        """Phase 2: Restore normal label colors after an error state."""
        self.labels['label1'].color = Config.get_color('row_one')
        self.labels['label2'].color = Config.get_color('row_two')
        self.labels['label3'].color = Config.get_color('row_three')
        debug_print("Label colors restored to normal")

    def show_status(self, message):
        """Show a status message."""
        self.display.show(self.text_group)
        self.clear_all_labels()
        self.set_label(1, message)
        log_info(f"Showing status: {message}")
