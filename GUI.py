"""
GUI Module for AI Business Meeting Assistant
Preserves backward compatibility with m1 floating pill widget while adding Live Meeting window.
"""
import tkinter as tk
import math
import logging
from typing import Callable, Optional

from desktop.gui import (
    FloatingPillWidget,
    MeetingAssistantWindow,
    apply_no_activate,
    HAVE_WIN32
)

logger = logging.getLogger(__name__)

# Global GUI singletons
floating_window: Optional[tk.Tk] = None
pill_widget: Optional[FloatingPillWidget] = None
meeting_window: Optional[MeetingAssistantWindow] = None
gui_state = "loading"
toggle_callback: Optional[Callable[[], None]] = None
open_meeting_callback: Optional[Callable[[], None]] = None


def is_point_in_assistant(x: int, y: int) -> bool:
    """Check if screen coordinate (x, y) is inside the floating pill window"""
    global floating_window
    if floating_window and floating_window.winfo_exists():
        try:
            wx = floating_window.winfo_rootx()
            wy = floating_window.winfo_rooty()
            ww = floating_window.winfo_width()
            wh = floating_window.winfo_height()
            return wx <= x <= wx + ww and wy <= y <= wy + wh
        except Exception:
            pass
    return False


def create_floating_window(
    cleanup_and_exit: Callable[[], None],
    on_toggle_recording: Optional[Callable[[], None]] = None,
    on_open_meeting: Optional[Callable[[], None]] = None
) -> tk.Tk:
    """Create and initialize the floating pill widget and main Tkinter instance"""
    global floating_window, pill_widget, toggle_callback, open_meeting_callback

    toggle_callback = on_toggle_recording
    open_meeting_callback = on_open_meeting

    floating_window = tk.Tk()
    pill_widget = FloatingPillWidget(
        root=floating_window,
        on_toggle_dictation=on_toggle_recording,
        on_open_meeting_window=on_open_meeting,
        on_cleanup_exit=cleanup_and_exit
    )
    return floating_window


def set_gui_state(state: str):
    """Update state on the floating pill widget: 'loading', 'idle', 'recording', 'processing', 'listening', 'analyzing'"""
    global gui_state, pill_widget, floating_window
    gui_state = state
    if pill_widget and floating_window and floating_window.winfo_exists():
        floating_window.after(0, lambda: pill_widget.set_state(state))


def start_animation():
    if pill_widget:
        pill_widget._start_animation()


def stop_animation():
    if pill_widget:
        pill_widget._stop_animation()


def draw_idle():
    set_gui_state("idle")
