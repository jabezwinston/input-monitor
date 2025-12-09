import os
import time
import tkinter as tk
from input_monitor.app import InputMonitorWidget
from pynput import mouse

import pytest

@pytest.mark.skipif('DISPLAY' not in os.environ, reason='No display available')
def test_middle_click_shows_middle_click():
    root = tk.Tk()
    try:
        widget = InputMonitorWidget(root)
        # Simulate middle click press
        widget.on_mouse_click(100, 200, mouse.Button.middle, pressed=True)
        # Allow any async operations to complete
        time.sleep(0.1)
        assert widget.input_label.cget('text') in ('Middle Click', 'Middle Double Click')
    finally:
        # Close the Tk instance
        widget.close_app()
        try:
            root.destroy()
        except Exception:
            pass


@pytest.mark.skipif('DISPLAY' not in os.environ, reason='No display available')
def test_double_click_detection_per_button():
    root = tk.Tk()
    try:
        widget = InputMonitorWidget(root)
        # Simulate left click press twice in quick succession to trigger double click
        widget.on_mouse_click(50, 50, mouse.Button.left, pressed=True)
        # set as release to simulate behavior
        widget.on_mouse_click(50, 50, mouse.Button.left, pressed=False)
        widget.on_mouse_click(50, 50, mouse.Button.left, pressed=True)
        assert widget.input_label.cget('text') == 'Left Double Click'

        # Now simulate a middle click at same position within double-click interval - should not be considered a middle double click
        widget.on_mouse_click(50, 50, mouse.Button.middle, pressed=True)
        assert widget.input_label.cget('text') == 'Middle Click'
    finally:
        widget.close_app()
        try:
            root.destroy()
        except Exception:
            pass


@pytest.mark.skipif('DISPLAY' not in os.environ, reason='No display available')
def test_shift_win_s_uses_inline_win_icon():
    root = tk.Tk()
    try:
        widget = InputMonitorWidget(root)
        # Ensure we have an icon assigned to test inline placement
        widget.win_icon = tk.PhotoImage(width=1, height=1)
        widget.win_icon_inline = widget.win_icon

        # Simulate Shift + Win + S presses in order
        widget.on_key_press('shift', event_time=1)
        widget.on_key_press('windows', event_time=2)
        widget.on_key_press('s', event_time=3)

        # Inline frame should be used and contain an image label with the win icon
        inline_children_images = [getattr(c, 'image', None) for c in widget._inline_children]
        assert any(img == widget.win_icon for img in inline_children_images)
        # Left icon should be empty when using inline icon
        assert widget.icon_label.image is None
    finally:
        widget.close_app()
        try:
            root.destroy()
        except Exception:
            pass
