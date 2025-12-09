import tkinter as tk
import tkinter.font as tkfont
import os
# 'font' module not required in this module; use tkinter font definitions inline where needed.
import time
import sys
from datetime import datetime
from pynput import mouse
import keyboard as kb
import threading
import re



class InputMonitorWidget:
    def __init__(self, root):
        self.root = root
        self.root.title("Input Monitor")
        
        # Make window borderless and topmost
        self.root.overrideredirect(True)
        self.root.attributes('-topmost', True)
        
        # Set initial position and size
        self.width = 360
        self.height = 180
        self.root.geometry(f"{self.width}x{self.height}+100+100")
        
        # Make window draggable
        self.root.bind("<ButtonPress-1>", self.start_drag)
        self.root.bind("<ButtonRelease-1>", self.stop_drag)
        self.root.bind("<B1-Motion>", self.on_drag)
        
        # Create UI elements
        self.frame = tk.Frame(root, bg='#2b2b2b', highlightbackground='#555555', highlightthickness=1)
        self.frame.pack(fill=tk.BOTH, expand=True)
        
        # Title label
        self.title_label = tk.Label(
            self.frame, 
            text="Input Monitor", 
            bg='#2b2b2b', 
            fg='white',
            font=('Arial', 10, 'bold')
        )
        self.title_label.pack(pady=5)
        
        # Input and icon display
        self.display_frame = tk.Frame(self.frame, bg='#2b2b2b')
        self.display_frame.pack(pady=2, padx=10, fill=tk.X)
        # Use a center_frame gridded into a 3-column layout to center contents
        self.display_frame.columnconfigure(0, weight=1)
        self.display_frame.columnconfigure(1, weight=0)
        self.display_frame.columnconfigure(2, weight=1)
        self.center_frame = tk.Frame(self.display_frame, bg='#2b2b2b')
        self.center_frame.grid(row=0, column=1)

        # Named fonts for consistent usage across labels
        self.font_input = tkfont.Font(family='Consolas', size=20)
        self.font_mouse = tkfont.Font(family='Consolas', size=10)
        # Make selection label larger at size 14 (user preference)
        self.font_selection = tkfont.Font(family='Consolas', size=14)
        self.font_time = tkfont.Font(family='Arial', size=8)

        # Icon label for event/keys
        self.icon_label = tk.Label(self.center_frame, bg='#2b2b2b')
        self.icon_label.pack(side=tk.LEFT, padx=(0, 6))

        # Input display
        self.input_label = tk.Label(
            self.center_frame,
            text="", 
            bg='#2b2b2b', 
            fg='#00ff00',
            font=self.font_input,
            wraplength=self.width-20
        )
        self.input_label.pack(side=tk.LEFT, pady=2)
        # Inline composition frame allows placing icons inline with text (e.g. Win icon between modifiers)
        self.inline_frame = tk.Frame(self.center_frame, bg='#2b2b2b')
        # Track any inline label widgets we create so they can be cleared
        self._inline_children = []
        
        # Timestamp display
        self.time_label = tk.Label(
            self.frame, 
            text="", 
            bg='#2b2b2b', 
            fg='#cccccc',
            font=self.font_time
        )
        self.time_label.pack(pady=2)
        
        # Mouse position display
        self.mouse_frame = tk.Frame(self.frame, bg='#2b2b2b')
        self.mouse_frame.pack(pady=2, padx=10, fill=tk.X)
        
        self.mouse_label = tk.Label(
            self.mouse_frame,
            text="X: 0, Y: 0 | ΔX: 0, ΔY: 0",
            bg='#2b2b2b',
            fg='#00ccff',
            font=self.font_mouse
        )
        self.mouse_label.pack(side=tk.LEFT)
        
        # Selection area display
        self.selection_frame = tk.Frame(self.frame, bg='#2b2b2b')
        self.selection_frame.pack(pady=2, padx=10, fill=tk.X)
        
        self.selection_label = tk.Label(
            self.selection_frame,
            text="Selection: 0 x 0",
            bg='#2b2b2b',
            fg='#ff9900',
            font=self.font_mouse
        )
        self.selection_label.pack(side=tk.LEFT)
        
        # Close button
        self.close_button = tk.Button(
            self.frame, 
            text="×", 
            command=self.close_app,
            bg='#2b2b2b', 
            fg='white', 
            bd=0,
            font=('Arial', 12, 'bold'),
            highlightthickness=0
        )
        self.close_button.place(x=self.width-25, y=5)
        
        # Initialize variables
        self._drag_start_x = 0
        self._drag_start_y = 0
        self.current_keys = set()
        self.key_press_order = []  # Track order of key presses as (key_name, timestamp)
        # Common Linux scan codes for left/right Meta (Win) keys (evdev KEY_LEFTMETA/KEY_RIGHTMETA)
        self.WIN_SCAN_CODES = {125, 126}
        self.last_click_time = 0
        self.last_click_pos = (0, 0)
        self.last_click_button = None
        self.reset_job = None
        
        # Mouse tracking
        self.last_mouse_x = 0
        self.last_mouse_y = 0
        self.mouse_update_counter = 0
        self.mouse_update_threshold = 5  # Update display every 5 mouse events
        
        # Selection tracking
        self.selection_start = None
        self.selection_end = None
        self.is_selecting = False
        
        # Key name mappings
        self.SPECIAL_KEYS = {
            'ctrl': 'Ctrl',
            'control': 'Ctrl',
            'alt': 'Alt',
            'alt gr': 'Alt',
            'lctrl': 'Ctrl',
            'rctrl': 'Ctrl',
            'lalt': 'Alt',
            'ralt': 'Alt',
            'shift': 'Shift',
            'lshift': 'Shift',
            'rshift': 'Shift',
            'windows': 'Win',
            'meta': 'Win',
            'leftmeta': 'Win',
            'rightmeta': 'Win',
            'super': 'Win',
            'lwin': 'Win',
            'rwin': 'Win',
            'cmd': 'Win',
            'space': 'Space',
            'enter': 'Enter',
            'tab': 'Tab',
            'esc': 'Esc',
            'up': 'Up ⬆',
            'down': 'Down ⬇',
            'left': 'Left ⬅',
            'right': 'Right ➡',
            'backspace': 'Backspace ←',
            'delete': 'Delete ⌫',
            'insert': 'Insert',
            'home': 'Home',
            'end': 'End',
            'print screen': 'Print Screen 📸',
            'page up': 'Page Up',
            'page down': 'Page Down',
            'caps lock': 'Caps Lock',
            'num lock': 'Num Lock',
            'f1': 'F1',
            'f2': 'F2',
            'f3': 'F3',
            'f4': 'F4',
            'f5': 'F5',
            'f6': 'F6',
            'f7': 'F7',
            'f8': 'F8',
            'f9': 'F9',
            'f10': 'F10',
            'f11': 'F11',
            'f12': 'F12',
        }
        
        # Setup event listeners
        self.setup_listeners()

        # Load icons
        self.load_icons()

    def load_icons(self):
        """Load image icons from the images directory if available."""
        try:
            # If bundled by PyInstaller, resources are extracted to sys._MEIPASS
            # Use that path if present. Otherwise, look for images relative
            # to the module file (normal installed or dev mode).
            if getattr(sys, '_MEIPASS', None):
                base_dir = os.path.join(getattr(sys, '_MEIPASS'), 'input_monitor', 'images')
            else:
                base_dir = os.path.join(os.path.dirname(__file__), 'images')
            win_path = os.path.join(base_dir, 'windows-10-logo.png')
            left_path = os.path.join(base_dir, 'mouse-left-click.png')
            right_path = os.path.join(base_dir, 'mouse-right-click.png')
            middle_path = os.path.join(base_dir, 'mouse-middle-click.png')

            # Tkinter PhotoImage supports PNG; subsample to a reasonable icon size if needed
            self.win_icon = tk.PhotoImage(file=win_path) if os.path.isfile(win_path) else None
            self.left_icon = tk.PhotoImage(file=left_path) if os.path.isfile(left_path) else None
            self.right_icon = tk.PhotoImage(file=right_path) if os.path.isfile(right_path) else None

            # Scale icons to desired target sizes to make mouse icons bigger
            def scale_icon(img, target_px):
                if img is None:
                    return None
                w, h = img.width(), img.height()
                max_dim = max(w, h)
                if max_dim == 0:
                    return img
                # If larger than target, subsample (integer downscale)
                if max_dim > target_px:
                    factor = max(1, max_dim // target_px)
                    return img.subsample(factor, factor)
                # If smaller than target, zoom up
                if max_dim < target_px:
                    factor = max(1, (target_px + max_dim - 1) // max_dim)
                    return img.zoom(factor, factor)
                return img

            # Use a slightly larger size for mouse icons so they are visually bigger
            self.win_icon = scale_icon(self.win_icon, 26)
            # Use a bigger target for mouse icons to be clearly visible
            self.left_icon = scale_icon(self.left_icon, 48)
            self.right_icon = scale_icon(self.right_icon, 48)
            self.middle_icon = tk.PhotoImage(file=middle_path) if os.path.isfile(middle_path) else None
            self.middle_icon = scale_icon(self.middle_icon, 48)
            # The Win icon may be reused as inline icon
            self.win_icon_inline = self.win_icon
        except Exception:
            # If any error occurs, simply don't use icons
            self.win_icon = None
            self.left_icon = None
            self.right_icon = None
    
    def setup_listeners(self):
        # Keyboard events using keyboard library
        self.keyboard_thread = threading.Thread(target=self.keyboard_listener, daemon=True)
        self.keyboard_thread.start()
        
        # Mouse events
        self.mouse_listener = mouse.Listener(
            on_move=self.on_mouse_move,
            on_click=self.on_mouse_click
        )
        self.mouse_listener.start()
    
    def keyboard_listener(self):
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
    
    def format_key_name(self, key_name):
        """Format key name for display"""
        # Normalize incoming key name and remove common punctuation
        key_name = key_name.lower().replace('-', ' ').replace('_', ' ').strip()
        
        # Normalize left/right modifier prefixes only for modifier keys (not arrow keys)
        parts = key_name.split()
        if len(parts) > 1 and parts[0] in ('left', 'right') and parts[1] in ('ctrl', 'control', 'shift', 'alt', 'alt gr', 'windows', 'super', 'cmd'):
            key_name = ' '.join(parts[1:])

        # Map common synonyms for modifier keys
        if key_name == 'control':
            key_name = 'ctrl'
        if key_name == 'super':
            key_name = 'windows'

        # Check if it's a special key
        if key_name in self.SPECIAL_KEYS:
            return self.SPECIAL_KEYS[key_name]
        
        # Handle special cases
        if key_name.startswith('ctrl + '):
            parts = key_name.split(' + ')
            formatted_parts = []
            for part in parts:
                formatted_parts.append(self.format_key_name(part))
            return ' + '.join(formatted_parts)
        
        # Handle single character keys
        if len(key_name) == 1 and key_name.isalpha():
            return key_name.upper()
        
        # Handle other keys
        return key_name.replace('_', ' ').title()
    
    def on_key_press(self, key_name, event_time=None, scan_code=None):
        # key_name here is the raw event.name reported by the keyboard library
        raw_name = key_name
        # Remap Linux Win/Meta key misreported as 'alt' by scan_code
        if scan_code is not None and scan_code in getattr(self, 'WIN_SCAN_CODES', set()):
            if isinstance(raw_name, str) and raw_name.lower().startswith('alt'):
                raw_name = 'windows'
        key_name = self.format_key_name(raw_name)
        if not key_name:  # Skip if we couldn't convert the key
            return
            
        # Remap common Linux case where the Windows key reports as 'alt' (scan_code 125/126)
        # Use the raw event name for the check since key_name may be the formatted display label
        if scan_code is not None and isinstance(raw_name, str) and raw_name.lower() in ('alt', 'alt gr') and scan_code in getattr(self, 'WIN_SCAN_CODES', set()):
            key_name = self.format_key_name('windows')

        if key_name not in self.current_keys:
            self.current_keys.add(key_name)
            if event_time is None:
                event_time = time.time()
            self.key_press_order.append((key_name, event_time))
        
        # Get modifiers and non-modifiers in the order they were pressed
        # Derive the order based on timestamps of key presses for reliability
        ordered_keys = [k for k, t in sorted(self.key_press_order, key=lambda x: x[1])]
        # Support 'Win' display string for the Windows key
        win_display_values = {'Win'}
        modifiers = [k for k in ordered_keys if k in ['Ctrl', 'Alt', 'Shift'] or k in win_display_values]
        non_modifiers = [k for k in ordered_keys if k not in (['Ctrl', 'Alt', 'Shift'] + list(win_display_values))]
        
        icon = None
        if non_modifiers:
            # Show the full combination
            keys = modifiers + non_modifiers
            key_text = " + ".join(keys)
            # If the keys contain Win, show the Win icon (even if combined)
            if any(k in win_display_values for k in keys):
                icon = getattr(self, 'win_icon', None)
            self.show_input(key_text, icon=icon)
        else:
            # Only modifiers pressed
            if modifiers:
                modifiers_text = " + ".join(modifiers)
                # If pressing only Win modifier, show icon
                if len(modifiers) == 1 and any(v in modifiers for v in win_display_values):
                    icon = getattr(self, 'win_icon', None)
                self.show_input(f"{modifiers_text} + ...", icon=icon)
    
    def on_key_release(self, key_name, event_time=None, scan_code=None):
        raw_name = key_name
        # Remap Linux Win/Meta key misreported as 'alt' by scan_code
        if scan_code is not None and scan_code in getattr(self, 'WIN_SCAN_CODES', set()):
            if isinstance(raw_name, str) and raw_name.lower().startswith('alt'):
                raw_name = 'windows'
        key_name = self.format_key_name(raw_name)
        # Remap Linux Win key reported as 'alt' using the original raw_name
        if scan_code is not None and isinstance(raw_name, str) and raw_name.lower() in ('alt', 'alt gr') and scan_code in getattr(self, 'WIN_SCAN_CODES', set()):
            key_name = self.format_key_name('windows')
        if key_name in self.current_keys:
            self.current_keys.remove(key_name)
            # Remove all matching entries for this key (should be at most one)
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
        if self.mouse_update_counter >= self.mouse_update_threshold:
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
    
    def on_mouse_click(self, x, y, button, pressed):
        if pressed:
            if button == mouse.Button.left:
                # Start selection
                self.selection_start = (x, y)
                self.is_selecting = True
                self.selection_label.config(text="Selection: 0 x 0")
                
                # Check for double click
                current_time = time.time()
                if (current_time - self.last_click_time < 0.5 and 
                    abs(x - self.last_click_pos[0]) < 5 and 
                    abs(y - self.last_click_pos[1]) < 5 and
                    self.last_click_button == mouse.Button.left):
                    self.show_input("Left Double Click", icon=getattr(self, 'left_icon', None))
                else:
                    self.show_input("Left Click", icon=getattr(self, 'left_icon', None))
                
                self.last_click_time = current_time
                self.last_click_pos = (x, y)
                self.last_click_button = mouse.Button.left
                
            elif button == mouse.Button.right:
                self.show_input("Right Click", icon=getattr(self, 'right_icon', None))
            elif button == mouse.Button.middle:
                current_time = time.time()
                if (current_time - self.last_click_time < 0.5 and 
                    abs(x - self.last_click_pos[0]) < 5 and 
                    abs(y - self.last_click_pos[1]) < 5 and
                    self.last_click_button == mouse.Button.middle):
                    self.show_input("Middle Double Click", icon=getattr(self, 'middle_icon', None))
                else:
                    self.show_input("Middle Click", icon=getattr(self, 'middle_icon', None))
                self.last_click_time = current_time
                self.last_click_pos = (x, y)
                self.last_click_button = mouse.Button.middle
        else:
            if button == mouse.Button.left and self.is_selecting:
                # End selection
                self.is_selecting = False
                if self.selection_start and self.selection_end:
                    width = abs(self.selection_end[0] - self.selection_start[0])
                    height = abs(self.selection_end[1] - self.selection_start[1])
                    
                    # Only show selection if it's significant
                    if width > 5 or height > 5:
                        self.show_input(f"Selected Area: {width} x {height}")
    
    def show_input(self, input_text, icon=None):
        # Cancel any pending reset
        if self.reset_job:
            self.root.after_cancel(self.reset_job)
            
        # Determine whether to display an inline icon with the Win key token inserted
        # Normalize for consistent matching
        token_to_replace = 'Win'
        # Clear any previous inline children
        for child in self._inline_children:
            try:
                child.destroy()
            except Exception:
                pass
        self._inline_children = []
        # If the display text contains the Win token and we have an icon, build inline labels
        if icon and re.search(r'\b' + re.escape(token_to_replace) + r'\b', input_text):
            # Hide the left icon when displaying inline
            self.icon_label.config(image='')
            self.icon_label.image = None
            # Hide the main input_label text so we'll use inline composition
            self.input_label.config(text='')
            # Ensure inline_frame is packed next to the label
            self.inline_frame.pack(side=tk.LEFT, pady=2)
            # Find the token position and split
            match = re.search(r'\b' + re.escape(token_to_replace) + r'\b', input_text)
            start, end = match.span()
            left_text = input_text[:start].rstrip()
            token_text = input_text[start:end]
            right_text = input_text[end:].lstrip()
            # Helper to create a label with given text
            def make_label(text):
                lbl = tk.Label(self.inline_frame, text=text, bg='#2b2b2b', fg='#00ff00', font=self.input_label.cget('font'))
                lbl.pack(side=tk.LEFT)
                self._inline_children.append(lbl)
                return lbl
            if left_text:
                make_label(left_text + ' ')
            # Token label
            make_label(token_text + ' ')
            # Icon label inline
            inline_icon_lbl = tk.Label(self.inline_frame, bg='#2b2b2b')
            inline_icon_lbl.pack(side=tk.LEFT, padx=(0, 6))
            inline_icon_lbl.config(image=icon)
            inline_icon_lbl.image = icon
            self._inline_children.append(inline_icon_lbl)
            if right_text:
                make_label(' ' + right_text)
        else:
            # If we had an inline frame previously, hide it
            try:
                self.inline_frame.pack_forget()
            except Exception:
                pass
            # Update the display with a single text label
            # If this is a 'Selected Area' message, show it with the selection font
            if input_text.startswith('Selected Area'):
                self.input_label.config(font=self.font_selection, text=input_text)
            else:
                # Ensure input label uses default font for normal messages
                self.input_label.config(font=self.font_input, text=input_text)
            # Update icon if provided, otherwise clear it
            if icon:
                self.icon_label.config(image=icon)
                self.icon_label.image = icon
            else:
                self.icon_label.config(image='')
                self.icon_label.image = None
        self.time_label.config(text=datetime.now().strftime("%H:%M:%S"))
        
        # Schedule a reset after 2 seconds
        self.reset_job = self.root.after(2000, self.reset_display)
    
    def reset_display(self):
        self.input_label.config(text="")
        # Restore default input font
        try:
            self.input_label.config(font=self.font_input)
        except Exception:
            pass
        self.time_label.config(text="")
        # Clear icon as well
        try:
            self.icon_label.config(image='')
            self.icon_label.image = None
        except Exception:
            pass
        self.reset_job = None
        # Clear inline frame
        for child in self._inline_children:
            try:
                child.destroy()
            except Exception:
                pass
        self._inline_children = []
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
