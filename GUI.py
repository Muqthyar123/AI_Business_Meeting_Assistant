import tkinter as tk
import math
import win32gui
import win32con
import win32process
import win32api
import ctypes
import time
import logging

logger = logging.getLogger(__name__)

# State variables
line_anim_state = 0
floating_window = None
canvas = None
animation_running = False
gui_state = "loading"  # "loading", "idle", "recording", "processing"
toggle_callback = None

# Audio visualizer lines configuration
line_heights = [10, 10, 10, 10]
max_height = 28
min_height = 6

def get_assistant_hwnds():
    """Return all HWNDs belonging to this assistant window"""
    hwnds = set()
    if floating_window:
        try:
            h = floating_window.winfo_id()
            hwnds.add(h)
            p = win32gui.GetParent(h)
            if p:
                hwnds.add(p)
            anc = win32gui.GetAncestor(h, 2)
            if anc:
                hwnds.add(anc)
        except Exception:
            pass
    return hwnds

def is_point_in_assistant(x, y):
    """Check if screen coordinate (x, y) is inside the floating window"""
    if floating_window:
        try:
            wx = floating_window.winfo_rootx()
            wy = floating_window.winfo_rooty()
            ww = floating_window.winfo_width()
            wh = floating_window.winfo_height()
            if wx <= x <= wx + ww and wy <= y <= wy + wh:
                return True
        except Exception:
            pass
    return False

def apply_no_activate(root):
    """Set WS_EX_NOACTIVATE style so clicks on this floating window never steal focus"""
    try:
        root.update_idletasks()
        h = root.winfo_id()
        p = win32gui.GetParent(h)
        for hwnd in [h, p]:
            if hwnd:
                style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
                win32gui.SetWindowLong(
                    hwnd,
                    win32con.GWL_EXSTYLE,
                    style | win32con.WS_EX_NOACTIVATE | win32con.WS_EX_TOPMOST
                )
    except Exception as e:
        logger.debug(f"apply_no_activate error: {e}")

def create_floating_window(cleanup_and_exit, on_toggle_recording=None):
    """Create a floating pill window"""
    global floating_window, canvas, animation_running, toggle_callback, gui_state

    toggle_callback = on_toggle_recording
    gui_state = "loading"

    floating_window = tk.Tk()
    floating_window.title("AI Voice Assistant")
    floating_window.configure(bg="#0b0c10")
    floating_window.attributes("-topmost", True)
    floating_window.resizable(False, False)
    floating_window.overrideredirect(True)

    window_width = 140
    window_height = 50

    screen_width = floating_window.winfo_screenwidth()
    x = (screen_width - window_width) // 2
    y = 60
    floating_window.geometry(f"{window_width}x{window_height}+{x}+{y}")

    floating_window._drag_data = {"x": 0, "y": 0}

    def on_drag_start(event):
        floating_window._drag_data["x"] = event.x
        floating_window._drag_data["y"] = event.y

    def on_drag_motion(event):
        deltax = event.x - floating_window._drag_data["x"]
        deltay = event.y - floating_window._drag_data["y"]
        new_x = floating_window.winfo_x() + deltax
        new_y = floating_window.winfo_y() + deltay
        floating_window.geometry(f"+{new_x}+{new_y}")

    floating_window.bind("<Button-1>", on_drag_start)
    floating_window.bind("<B1-Motion>", on_drag_motion)

    main_frame = tk.Frame(floating_window, bg="#0b0c10")
    main_frame.pack(fill="both", expand=True)

    canvas = tk.Canvas(
        main_frame,
        width=window_width,
        height=window_height,
        bg="#0b0c10",
        highlightthickness=0
    )
    canvas.pack(fill="both", expand=True)

    canvas.bind("<Button-1>", lambda event: on_canvas_click(event, cleanup_and_exit))
    canvas.bind("<Button-3>", lambda e: cleanup_and_exit())

    draw_ui()
    apply_no_activate(floating_window)

    return floating_window

def on_canvas_click(event, cleanup_and_exit):
    """Handle click on canvas: Play/Stop button, close, or drag"""
    global toggle_callback, gui_state
    
    # 1. Close button check (top right: x>=118, y<=20)
    if event.x >= 118 and event.y <= 20:
        cleanup_and_exit()
        return

    # 2. Play/Stop button center is at (30, 25) with radius 18
    dx = event.x - 30
    dy = event.y - 25
    if math.sqrt(dx*dx + dy*dy) <= 22:
        if gui_state == "loading":
            return
        if toggle_callback:
            toggle_callback()
    else:
        floating_window._drag_data = {"x": event.x, "y": event.y}

def set_gui_state(state):
    """Set state: 'loading', 'idle', 'recording', 'processing'"""
    global gui_state, floating_window
    gui_state = state
    if state == "recording":
        start_animation()
    else:
        stop_animation()
    if floating_window:
        floating_window.after(0, draw_ui)
    else:
        draw_ui()

def draw_ui():
    """Redraw the floating pill widget"""
    global canvas, gui_state
    if not canvas or not canvas.winfo_exists():
        return

    canvas.delete("all")
    w = 140
    h = 50

    # 1. Pill shape container
    draw_rounded_rect(2, 2, w - 2, h - 2, radius=18, fill="#12141d", outline="#25293a", width=1.5)

    # 2. Play / Stop / Loading Button at (30, 25)
    btn_x, btn_y = 30, 25
    btn_r = 16

    if gui_state == "loading":
        canvas.create_oval(btn_x - btn_r, btn_y - btn_r, btn_x + btn_r, btn_y + btn_r,
                          fill="#181d28", outline="#4a5568", width=1.5, tags="btn")
        canvas.create_text(btn_x, btn_y, text="⌛", fill="#8a99ad", font=("Segoe UI Emoji", 10))
        canvas.create_text(85, btn_y, text="Loading...", fill="#8a99ad", font=("Segoe UI", 9, "italic"))

    elif gui_state == "idle":
        canvas.create_oval(btn_x - btn_r, btn_y - btn_r, btn_x + btn_r, btn_y + btn_r,
                          fill="#0f2b38", outline="#00e5ff", width=1.5, tags="btn")
        # Play Triangle (▶)
        tri_pts = [btn_x - 4, btn_y - 7, btn_x + 8, btn_y, btn_x - 4, btn_y + 7]
        canvas.create_polygon(tri_pts, fill="#00e5ff", tags="btn")
        draw_visualizer_lines()

    elif gui_state == "recording":
        # Outer pulsating ring
        canvas.create_oval(btn_x - btn_r - 2, btn_y - btn_r - 2, btn_x + btn_r + 2, btn_y + btn_r + 2,
                          fill="", outline="#ff5252", width=1, tags="btn")
        canvas.create_oval(btn_x - btn_r, btn_y - btn_r, btn_x + btn_r, btn_y + btn_r,
                          fill="#3d1418", outline="#ff5252", width=1.5, tags="btn")
        # Stop Square (■)
        sq = 5
        canvas.create_rectangle(btn_x - sq, btn_y - sq, btn_x + sq, btn_y + sq,
                               fill="#ff5252", outline="", tags="btn")
        draw_visualizer_lines()

    elif gui_state == "processing":
        canvas.create_oval(btn_x - btn_r, btn_y - btn_r, btn_x + btn_r, btn_y + btn_r,
                          fill="#33250f", outline="#ffb74d", width=1.5, tags="btn")
        canvas.create_text(btn_x, btn_y - 1, text="...", fill="#ffb74d", font=("Consolas", 12, "bold"))
        draw_visualizer_lines()

    # Close button at top right (x=128, y=12)
    canvas.create_text(126, 12, text="✕", fill="#5a607a", font=("Arial", 8, "bold"), tags="close")

def draw_visualizer_lines():
    """Draw audio visualizer lines on the right side of the pill"""
    global canvas, line_heights, gui_state
    if not canvas:
        return

    canvas.delete("lines")
    center_y = 25
    x_coords = [62, 75, 88, 101]
    line_w = 4

    color = "#00e5ff" if gui_state == "recording" else ("#ffb74d" if gui_state == "processing" else "#252b3d")

    for i, x in enumerate(x_coords):
        lh = int(line_heights[i])
        y1 = center_y - lh // 2
        y2 = center_y + lh // 2
        canvas.create_line(x, y1, x, y2, fill=color, width=line_w, capstyle="round", tags="lines")

def draw_rounded_rect(x1, y1, x2, y2, radius=15, **kwargs):
    """Utility to draw a rounded rectangle on Tkinter canvas"""
    global canvas
    points = [
        x1 + radius, y1,
        x2 - radius, y1,
        x2, y1,
        x2, y1 + radius,
        x2, y2 - radius,
        x2, y2,
        x2 - radius, y2,
        x1 + radius, y2,
        x1, y2,
        x1, y2 - radius,
        x1, y1 + radius,
        x1, y1
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)

def start_animation():
    """Start line height animation when recording starts"""
    global animation_running, floating_window
    if not animation_running:
        animation_running = True
        if floating_window:
            floating_window.after(40, animate_lines)

def stop_animation():
    """Stop line animation and return to idle heights"""
    global animation_running, line_heights
    animation_running = False
    line_heights = [10, 10, 10, 10]

def animate_lines():
    """Animate visualizer lines with sine wave while recording"""
    global line_anim_state, animation_running, floating_window, canvas, line_heights, gui_state
    if not animation_running or not canvas:
        return

    time_val = line_anim_state * 0.25
    for i in range(4):
        phase = i * math.pi / 2
        freq = 1.6 + i * 0.2
        amplitude = (max_height - min_height) / 2
        line_heights[i] = min_height + amplitude + amplitude * math.sin(time_val * freq + phase)

    line_anim_state += 1
    draw_ui()

    if animation_running and floating_window:
        floating_window.after(40, animate_lines)

def draw_idle():
    """Reset to idle state"""
    set_gui_state("idle")