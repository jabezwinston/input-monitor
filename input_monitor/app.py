import tkinter as tk
import tkinter.font as tkfont
import os
import time
import sys
from datetime import datetime
from pynput import mouse
import keyboard as kb
import threading
import re

class InputMonitorWidget:
    # UI Configuration
    WINDOW_WIDTH = 360
    WINDOW_HEIGHT = 180
    WINDOW_INITIAL_X = 100
    WINDOW_INITIAL_Y = 100
    
    # Colors
    BG_COLOR = '#2b2b2b'
    BORDER_COLOR = '#555555'
    TEXT_COLOR = 'white'
    INPUT_COLOR = '#00ff00'
    TIME_COLOR = '#cccccc'
    MOUSE_COLOR = '#00ccff'
    SELECTION_COLOR = '#ff9900'
    
    # Timing
    RESET_DELAY_MS = 2000
    DOUBLE_CLICK_THRESHOLD = 0.5
    DOUBLE_CLICK_POSITION_TOLERANCE = 5
    
    # Mouse tracking
    MOUSE_UPDATE_THRESHOLD = 5
    SELECTION_MIN_SIZE = 5
    
    # Icon sizes
    WIN_ICON_SIZE = 26
    MOUSE_ICON_SIZE = 48
    
    # Linux scan codes for Win/Meta keys
    WIN_SCAN_CODES = {125, 126}
    
    # Modifier keys
    MODIFIERS = {'Ctrl', 'Alt', 'Shift', 'Win'}
    
    def __init__(self, root):
        self.root = root
        self.root.title("Input Monitor")
        
        # Make window borderless and topmost
        self.root.overrideredirect(True)
        self.root.attributes('-topmost', True)
        
        # Set initial position and size
        self.width = self.WINDOW_WIDTH
        self.height = self.WINDOW_HEIGHT
        self.root.geometry(f"{self.width}x{self.height}+{self.WINDOW_INITIAL_X}+{self.WINDOW_INITIAL_Y}")
        
        # Make window draggable
        self.root.bind("<ButtonPress-1>", self.start_drag)
        self.root.bind("<ButtonRelease-1>", self.stop_drag)
        self.root.bind("<B1-Motion>", self.on_drag)
        
        # Initialize state variables
        self._init_state_variables()
        
        # Create UI elements
        self.frame = tk.Frame(root, bg=self.BG_COLOR, highlightbackground=self.BORDER_COLOR, highlightthickness=1)
        self.frame.pack(fill=tk.BOTH, expand=True)
        
        # Setup UI components
        self._setup_title()
        self._setup_input_display()
        self._setup_timestamp_display()
        self._setup_mouse_display()
        self._setup_selection_display()
        self._setup_close_button()
        
        # Setup event listeners
        self._setup_listeners()
        
        # Load icons
        self._load_icons()
    
    def _init_state_variables(self):
        """Initialize all state tracking variables."""
        # Dragging
        self._drag_start_x = 0
        self._drag_start_y = 0
        
        # Keyboard state
        self.current_keys = set()
        self.key_press_order = []
        
        # Click tracking
        self.last_click_time = 0
        self.last_click_pos = (0, 0)
        self.last_click_button = None
        self.reset_job = None
        
        # Mouse tracking
        self.last_mouse_x = 0
        self.last_mouse_y = 0
        self.mouse_update_counter = 0
        
        # Selection tracking
        self.selection_start = None
        self.selection_end = None
        self.is_selecting = False
        
        # Inline UI children
        self._inline_children = []
    
    def _setup_title(self):
        """Create the title label."""
        self.title_label = tk.Label(
            self.frame, 
            text="Input Monitor", 
            bg=self.BG_COLOR, 
            fg=self.TEXT_COLOR,
            font=('Arial', 10, 'bold')
        )
        self.title_label.pack(pady=5)
    
    def _setup_input_display(self):
        """Create the input and icon display area."""
        self.display_frame = tk.Frame(self.frame, bg=self.BG_COLOR)
        self.display_frame.pack(pady=2, padx=10, fill=tk.X)
        
        # Use a center_frame gridded into a 3-column layout to center contents
        self.display_frame.columnconfigure(0, weight=1)
        self.display_frame.columnconfigure(1, weight=0)
        self.display_frame.columnconfigure(2, weight=1)
        self.center_frame = tk.Frame(self.display_frame, bg=self.BG_COLOR)
        self.center_frame.grid(row=0, column=1)

        # Named fonts for consistent usage across labels
        self.font_input = tkfont.Font(family='Consolas', size=20)
        self.font_mouse = tkfont.Font(family='Consolas', size=10)
        self.font_selection = tkfont.Font(family='Consolas', size=14)
        self.font_time = tkfont.Font(family='Arial', size=8)

        # Icon label for event/keys
        self.icon_label = tk.Label(self.center_frame, bg=self.BG_COLOR)
        self.icon_label.pack(side=tk.LEFT, padx=(0, 6))

        # Input display
        self.input_label = tk.Label(
            self.center_frame,
            text="", 
            bg=self.BG_COLOR, 
            fg=self.INPUT_COLOR,
            font=self.font_input,
            wraplength=self.width-20
        )
        self.input_label.pack(side=tk.LEFT, pady=2)
        
        # Inline composition frame allows placing icons inline with text
        self.inline_frame = tk.Frame(self.center_frame, bg=self.BG_COLOR)
    
    def _setup_timestamp_display(self):
        """Create the timestamp display."""
        self.time_label = tk.Label(
            self.frame, 
            text="", 
            bg=self.BG_COLOR, 
            fg=self.TIME_COLOR,
            font=self.font_time
        )
        self.time_label.pack(pady=2)
    
    def _setup_mouse_display(self):
        """Create the mouse position display."""
        self.mouse_frame = tk.Frame(self.frame, bg=self.BG_COLOR)
        self.mouse_frame.pack(pady=2, padx=10, fill=tk.X)
        
        self.mouse_label = tk.Label(
            self.mouse_frame,
            text="X: 0, Y: 0 | ΔX: 0, ΔY: 0",
            bg=self.BG_COLOR,
            fg=self.MOUSE_COLOR,
            font=self.font_mouse
        )
        self.mouse_label.pack(side=tk.LEFT)
    
    def _setup_selection_display(self):
        """Create the selection area display."""
        self.selection_frame = tk.Frame(self.frame, bg=self.BG_COLOR)
        self.selection_frame.pack(pady=2, padx=10, fill=tk.X)
        
        self.selection_label = tk.Label(
            self.selection_frame,
            text="Selection: 0 x 0",
            bg=self.BG_COLOR,
            fg=self.SELECTION_COLOR,
            font=self.font_mouse
        )
        self.selection_label.pack(side=tk.LEFT)
    
    def _setup_close_button(self):
        """Create the close button."""
        self.close_button = tk.Button(
            self.frame, 
            text="×", 
            command=self.close_app,
            bg=self.BG_COLOR, 
            fg=self.TEXT_COLOR, 
            bd=0,
            font=('Arial', 12, 'bold'),
            highlightthickness=0
        )
        self.close_button.place(x=self.width-25, y=5)
        
        # Make window draggable
        self.root.bind("<ButtonPress-1>", self.start_drag)
        self.root.bind("<ButtonRelease-1>", self.stop_drag)
        self.root.bind("<B1-Motion>", self.on_drag)
    
    def _setup_listeners(self):
        """Setup keyboard and mouse event listeners."""
        # Keyboard events using keyboard library
        self.keyboard_thread = threading.Thread(target=self._keyboard_listener, daemon=True)
        self.keyboard_thread.start()
        
        # Mouse events
        self.mouse_listener = mouse.Listener(
            on_move=self.on_mouse_move,
            on_click=self.on_mouse_click
        )
        self.mouse_listener.start()
    
    def _load_icons(self):
        """Load image icons from the images directory if available."""
        try:
            base_dir = self._get_icons_directory()
            
            # Load icon files
            icon_files = {
                'win': 'windows-10-logo.png',
                'left': 'mouse-left-click.png',
                'right': 'mouse-right-click.png',
                'middle': 'mouse-middle-click.png'
            }
            
            icons = {}
            for key, filename in icon_files.items():
                path = os.path.join(base_dir, filename)
                icons[key] = tk.PhotoImage(file=path) if os.path.isfile(path) else None
            
            # Scale icons to target sizes
            self.win_icon = self._scale_icon(icons['win'], self.WIN_ICON_SIZE)
            self.left_icon = self._scale_icon(icons['left'], self.MOUSE_ICON_SIZE)
            self.right_icon = self._scale_icon(icons['right'], self.MOUSE_ICON_SIZE)
            self.middle_icon = self._scale_icon(icons['middle'], self.MOUSE_ICON_SIZE)
            self.win_icon_inline = self.win_icon
        except Exception:
            # If any error occurs, simply don't use icons
            self.win_icon = None
            self.left_icon = None
            self.right_icon = None
            self.middle_icon = None
    
    def _get_icons_directory(self):
        """Get the directory containing icon images."""
        if getattr(sys, '_MEIPASS', None):
            return os.path.join(getattr(sys, '_MEIPASS'), 'input_monitor', 'images')
        return os.path.join(os.path.dirname(__file__), 'images')
    
    def _scale_icon(self, img, target_px):
        """Scale an icon to the target size."""
        if img is None:
            return None
        
        w, h = img.width(), img.height()
        max_dim = max(w, h)
        
        if max_dim == 0:
            return img
        
        if max_dim > target_px:
            # Downscale
            factor = max(1, max_dim // target_px)
            return img.subsample(factor, factor)
        elif max_dim < target_px:
            # Upscale
            factor = max(1, (target_px + max_dim - 1) // max_dim)
            return img.zoom(factor, factor)
        
        return img
    
    def _keyboard_listener(self):
        """Listen for keyboard events using keyboard library"""
        while True:
            try:
                event = kb.read_event()
            except ImportError:
                # keyboard library cannot be used on this system (e.g., requires root on Linux)
                return
            except Exception:
                # Ignore transient exceptions and try again
                time.sleep(0.1)
                continue
            if event.event_type == kb.KEY_DOWN:
                # Pass event time and scan_code along so we can order by actual press time and handle Linux meta key
                self.on_key_press(event.name, getattr(event, 'time', None), getattr(event, 'scan_code', None))
            elif event.event_type == kb.KEY_UP:
                self.on_key_release(event.name, getattr(event, 'time', None), getattr(event, 'scan_code', None))
    
    # Key name mappings
    SPECIAL_KEYS = {
        'ctrl': 'Ctrl', 'control': 'Ctrl', 'lctrl': 'Ctrl', 'rctrl': 'Ctrl',
        'alt': 'Alt', 'alt gr': 'Alt', 'lalt': 'Alt', 'ralt': 'Alt',
        'shift': 'Shift', 'lshift': 'Shift', 'rshift': 'Shift',
        'windows': 'Win', 'meta': 'Win', 'leftmeta': 'Win', 'rightmeta': 'Win',
        'super': 'Win', 'lwin': 'Win', 'rwin': 'Win', 'cmd': 'Win',
        'space': 'Space', 'enter': 'Enter', 'tab': 'Tab', 'esc': 'Esc',
        'up': 'Up ⬆', 'down': 'Down ⬇', 'left': 'Left ⬅', 'right': 'Right ➡',
        'backspace': 'Backspace ←', 'delete': 'Delete ⌫',
        'insert': 'Insert', 'home': 'Home', 'end': 'End',
        'print screen': 'Print Screen 📸',
        'page up': 'Page Up', 'page down': 'Page Down',
        'caps lock': 'Caps Lock', 'num lock': 'Num Lock',
        'f1': 'F1', 'f2': 'F2', 'f3': 'F3', 'f4': 'F4', 'f5': 'F5', 'f6': 'F6',
        'f7': 'F7', 'f8': 'F8', 'f9': 'F9', 'f10': 'F10', 'f11': 'F11', 'f12': 'F12',
    }
    
    def format_key_name(self, key_name):
        """Format key name for display."""
        # Normalize incoming key name
        key_name = key_name.lower().replace('-', ' ').replace('_', ' ').strip()
        
        # Remove left/right prefix for modifiers only
        parts = key_name.split()
        if len(parts) > 1 and parts[0] in ('left', 'right'):
            if parts[1] in ('ctrl', 'control', 'shift', 'alt', 'alt gr', 'windows', 'super', 'cmd'):
                key_name = ' '.join(parts[1:])
        
        # Check special keys mapping
        if key_name in self.SPECIAL_KEYS:
            return self.SPECIAL_KEYS[key_name]
        
        # Single character keys
        if len(key_name) == 1 and key_name.isalpha():
            return key_name.upper()
        
        # Default formatting
        return key_name.title()
    
    def _normalize_win_key(self, raw_name, scan_code):
        """Normalize Linux Win/Meta key that may be misreported as 'alt'."""
        if scan_code in self.WIN_SCAN_CODES:
            if isinstance(raw_name, str) and raw_name.lower().replace(' ', '') in ('alt', 'altgr'):
                return 'windows'
        return raw_name
    
    def on_key_press(self, key_name, event_time=None, scan_code=None):
        """Handle key press events."""
        # Normalize Linux Win key handling
        raw_name = self._normalize_win_key(key_name, scan_code)
        key_name = self.format_key_name(raw_name)
        
        if not key_name:
            return
        
        # Track key press
        if key_name not in self.current_keys:
            self.current_keys.add(key_name)
            self.key_press_order.append((key_name, event_time or time.time()))
        
        # Build and display key combination
        self._display_key_combination()
    
    def _display_key_combination(self):
        """Display the current key combination."""
        ordered_keys = [k for k, t in sorted(self.key_press_order, key=lambda x: x[1])]
        modifiers = [k for k in ordered_keys if k in self.MODIFIERS]
        non_modifiers = [k for k in ordered_keys if k not in self.MODIFIERS]
        
        icon = None
        has_win = 'Win' in modifiers or 'Win' in non_modifiers
        
        if non_modifiers:
            keys = modifiers + non_modifiers
            key_text = " + ".join(keys)
            if has_win:
                icon = getattr(self, 'win_icon', None)
            self.show_input(key_text, icon=icon)
        elif modifiers:
            modifiers_text = " + ".join(modifiers)
            if len(modifiers) == 1 and has_win:
                icon = getattr(self, 'win_icon', None)
            self.show_input(f"{modifiers_text} + ...", icon=icon)
    
    def on_key_release(self, key_name, event_time=None, scan_code=None):
        """Handle key release events."""
        raw_name = self._normalize_win_key(key_name, scan_code)
        key_name = self.format_key_name(raw_name)
        
        if key_name in self.current_keys:
            self.current_keys.remove(key_name)
            self.key_press_order = [(k, t) for (k, t) in self.key_press_order if k != key_name]
    
    def on_mouse_move(self, x, y):
        # Calculate delta
        delta_x = x - self.last_mouse_x
        delta_y = y - self.last_mouse_y
        
        # Update last position
        self.last_mouse_x = x
        self.last_mouse_y = y
        
        # Update counter
        self.mouse_update_counter += 1
        
        # Update display every few events to avoid too frequent updates
        if self.mouse_update_counter >= self.MOUSE_UPDATE_THRESHOLD:
            self.mouse_update_counter = 0
            self.mouse_label.config(
                text=f"X: {x}, Y: {y} | ΔX: {delta_x}, ΔY: {delta_y}"
            )
        
        # Update selection if we're in the middle of selecting
        if self.is_selecting and self.selection_start:
            self.selection_end = (x, y)
            width = abs(self.selection_end[0] - self.selection_start[0])
            height = abs(self.selection_end[1] - self.selection_start[1])
            self.selection_label.config(text=f"Selection: {width} x {height}")
    
    def _is_double_click(self, x, y, button, current_time):
        """Check if this is a double click."""
        return (current_time - self.last_click_time < self.DOUBLE_CLICK_THRESHOLD and
                abs(x - self.last_click_pos[0]) < self.DOUBLE_CLICK_POSITION_TOLERANCE and
                abs(y - self.last_click_pos[1]) < self.DOUBLE_CLICK_POSITION_TOLERANCE and
                self.last_click_button == button)
    
    def on_mouse_click(self, x, y, button, pressed):
        """Handle mouse click events."""
        if pressed:
            current_time = time.time()
            
            if button == mouse.Button.left:
                self._handle_left_click(x, y, current_time)
            elif button == mouse.Button.right:
                self.show_input("Right Click", icon=getattr(self, 'right_icon', None))
            elif button == mouse.Button.middle:
                self._handle_middle_click(x, y, current_time)
        else:
            if button == mouse.Button.left and self.is_selecting:
                self._end_selection()
    
    def _handle_left_click(self, x, y, current_time):
        """Handle left mouse button click."""
        # Start selection
        self.selection_start = (x, y)
        self.is_selecting = True
        self.selection_label.config(text="Selection: 0 x 0")
        
        # Check for double click
        if self._is_double_click(x, y, mouse.Button.left, current_time):
            self.show_input("Left Double Click", icon=getattr(self, 'left_icon', None))
        else:
            self.show_input("Left Click", icon=getattr(self, 'left_icon', None))
        
        self.last_click_time = current_time
        self.last_click_pos = (x, y)
        self.last_click_button = mouse.Button.left
    
    def _handle_middle_click(self, x, y, current_time):
        """Handle middle mouse button click."""
        if self._is_double_click(x, y, mouse.Button.middle, current_time):
            self.show_input("Middle Double Click", icon=getattr(self, 'middle_icon', None))
        else:
            self.show_input("Middle Click", icon=getattr(self, 'middle_icon', None))
        
        self.last_click_time = current_time
        self.last_click_pos = (x, y)
        self.last_click_button = mouse.Button.middle
    
    def _end_selection(self):
        """End the current selection."""
        self.is_selecting = False
        if self.selection_start and self.selection_end:
            width = abs(self.selection_end[0] - self.selection_start[0])
            height = abs(self.selection_end[1] - self.selection_start[1])
            
            if width > self.SELECTION_MIN_SIZE or height > self.SELECTION_MIN_SIZE:
                self.show_input(f"Selected Area: {width} x {height}")
    
    def show_input(self, input_text, icon=None):
        """Display input text and optional icon."""
        # Cancel any pending reset
        if self.reset_job:
            self.root.after_cancel(self.reset_job)
        
        self._clear_inline_children()
        
        # Check if we should display inline (Win key with icon)
        if icon and 'Win' in input_text:
            self._display_inline_icon(input_text, icon)
        else:
            self._display_standard(input_text, icon)
        
        self.time_label.config(text=datetime.now().strftime("%H:%M:%S"))
        self.reset_job = self.root.after(self.RESET_DELAY_MS, self.reset_display)
    
    def _clear_inline_children(self):
        """Clear all inline child widgets."""
        for child in self._inline_children:
            try:
                child.destroy()
            except Exception:
                pass
        self._inline_children = []
    
    def _display_inline_icon(self, input_text, icon):
        """Display text with inline Win icon."""
        match = re.search(r'\bWin\b', input_text)
        if not match:
            self._display_standard(input_text, icon)
            return
        
        self.icon_label.config(image='')
        self.icon_label.image = None
        self.input_label.config(text='')
        self.inline_frame.pack(side=tk.LEFT, pady=2)
        
        start, end = match.span()
        left_text = input_text[:start].rstrip()
        token_text = input_text[start:end]
        right_text = input_text[end:].lstrip()
        
        def make_label(text):
            lbl = tk.Label(self.inline_frame, text=text, bg=self.BG_COLOR, fg=self.INPUT_COLOR, 
                         font=self.input_label.cget('font'))
            lbl.pack(side=tk.LEFT)
            self._inline_children.append(lbl)
        
        if left_text:
            make_label(left_text + ' ')
        make_label(token_text + ' ')
        
        # Icon inline
        icon_lbl = tk.Label(self.inline_frame, bg=self.BG_COLOR, image=icon)
        icon_lbl.image = icon
        icon_lbl.pack(side=tk.LEFT, padx=(0, 6))
        self._inline_children.append(icon_lbl)
        
        if right_text:
            make_label(' ' + right_text)
    
    def _display_standard(self, input_text, icon):
        """Display text in standard format."""
        try:
            self.inline_frame.pack_forget()
        except Exception:
            pass
        
        # Use selection font for 'Selected Area' messages
        font = self.font_selection if input_text.startswith('Selected Area') else self.font_input
        self.input_label.config(font=font, text=input_text)
        
        # Update icon
        if icon:
            self.icon_label.config(image=icon)
            self.icon_label.image = icon
        else:
            self.icon_label.config(image='')
            self.icon_label.image = None
    
    def reset_display(self):
        """Reset the display to empty state."""
        self.input_label.config(text="", font=self.font_input)
        self.time_label.config(text="")
        self.icon_label.config(image='')
        self.icon_label.image = None
        self.reset_job = None
        
        self._clear_inline_children()
        try:
            self.inline_frame.pack_forget()
        except Exception:
            pass
    
    def start_drag(self, event):
        self._drag_start_x = event.x
        self._drag_start_y = event.y
    
    def stop_drag(self, event):
        self._drag_start_x = 0
        self._drag_start_y = 0
    
    def on_drag(self, event):
        x = self.root.winfo_x() + event.x - self._drag_start_x
        y = self.root.winfo_y() + event.y - self._drag_start_y
        self.root.geometry(f"+{x}+{y}")
    
    def close_app(self):
        self.mouse_listener.stop()
        self.root.destroy()


def main():
    """Entry point for CLI or Python module execution. Starts the GUI loop."""
    root = tk.Tk()
    # Keep a persistent reference to the widget on the root to avoid
    # being garbage-collected and to allow access from external code.
    root._app = InputMonitorWidget(root)
    root.mainloop()


if __name__ == "__main__":
    main()
