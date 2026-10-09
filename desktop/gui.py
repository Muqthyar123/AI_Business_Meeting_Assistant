import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import math
import logging
import threading
import time
import os
import json
from typing import Callable, Optional, Dict, Any, List

# Windows-specific API for non-activating floating windows
HAVE_WIN32 = False
try:
    import win32gui
    import win32con
    import ctypes
    HAVE_WIN32 = True
except Exception:
    pass

logger = logging.getLogger(__name__)


def apply_no_activate(window: tk.Tk):
    """Set WS_EX_NOACTIVATE so clicks on floating widgets don't steal focus from meeting apps"""
    if not HAVE_WIN32:
        return
    try:
        window.update_idletasks()
        hwnd = window.winfo_id()
        parent = win32gui.GetParent(hwnd)
        for h in [hwnd, parent]:
            if h:
                style = win32gui.GetWindowLong(h, win32con.GWL_EXSTYLE)
                win32gui.SetWindowLong(
                    h,
                    win32con.GWL_EXSTYLE,
                    style | win32con.WS_EX_NOACTIVATE | win32con.WS_EX_TOPMOST
                )
    except Exception as e:
        logger.debug(f"apply_no_activate error: {e}")


class FloatingPillWidget:
    """Compact floating pill widget for voice dictation and meeting control"""

    def __init__(
        self,
        root: tk.Tk,
        on_toggle_dictation: Optional[Callable[[], None]] = None,
        on_open_meeting_window: Optional[Callable[[], None]] = None,
        on_cleanup_exit: Optional[Callable[[], None]] = None,
    ):
        self.root = root
        self.on_toggle_dictation = on_toggle_dictation
        self.on_open_meeting_window = on_open_meeting_window
        self.on_cleanup_exit = on_cleanup_exit

        self.gui_state = "loading"  # loading, idle, recording, processing, listening, analyzing, completed
        self.line_heights = [10, 10, 10, 10]
        self.animation_running = False
        self.anim_frame = 0

        self.w = 180
        self.h = 50

        self._init_window()
        self._create_widgets()

    def _init_window(self):
        self.root.title("AI Meeting Assistant")
        self.root.configure(bg="#0b0c10")
        self.root.attributes("-topmost", True)
        self.root.resizable(False, False)
        self.root.overrideredirect(True)

        screen_w = self.root.winfo_screenwidth()
        x = (screen_w - self.w) // 2
        y = 40
        self.root.geometry(f"{self.w}x{self.h}+{x}+{y}")

        # Dragging support
        self._drag_data = {"x": 0, "y": 0}
        self.root.bind("<Button-1>", self._on_drag_start)
        self.root.bind("<B1-Motion>", self._on_drag_motion)

    def _create_widgets(self):
        self.canvas = tk.Canvas(
            self.root,
            width=self.w,
            height=self.h,
            bg="#0b0c10",
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Button-1>", self._on_canvas_click)
        self.canvas.bind("<Button-3>", lambda e: self.on_cleanup_exit() if self.on_cleanup_exit else None)

        self.redraw()
        apply_no_activate(self.root)

    def _on_drag_start(self, event):
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def _on_drag_motion(self, event):
        dx = event.x - self._drag_data["x"]
        dy = event.y - self._drag_data["y"]
        nx = self.root.winfo_x() + dx
        ny = self.root.winfo_y() + dy
        self.root.geometry(f"+{nx}+{ny}")

    def _on_canvas_click(self, event):
        x, y = event.x, event.y

        # Close button (top right: x >= 160, y <= 20)
        if x >= self.w - 20 and y <= 20:
            if self.on_cleanup_exit:
                self.on_cleanup_exit()
            return

        # Meeting Dashboard Button (center-right: x 115..155, y 12..38)
        if 115 <= x <= 155 and 12 <= y <= 38:
            if self.on_open_meeting_window:
                self.on_open_meeting_window()
            return

        # Play/Record Button at (28, 25) with radius 18
        dx = x - 28
        dy = y - 25
        if math.hypot(dx, dy) <= 22:
            if self.gui_state != "loading" and self.on_toggle_dictation:
                self.on_toggle_dictation()
        else:
            self._drag_data = {"x": x, "y": y}

    def set_state(self, state: str):
        self.gui_state = state
        if state in ("recording", "listening"):
            self._start_animation()
        else:
            self._stop_animation()
        self.root.after(0, self.redraw)

    def redraw(self):
        if not self.canvas or not self.canvas.winfo_exists():
            return

        self.canvas.delete("all")
        w, h = self.w, self.h

        # Pill background container
        self._draw_rounded_rect(2, 2, w - 2, h - 2, radius=18, fill="#12141d", outline="#25293a", width=1.5)

        # Primary Action Button at (28, 25)
        bx, by, br = 28, 25, 16
        if self.gui_state == "loading":
            self.canvas.create_oval(bx - br, by - br, bx + br, by + br, fill="#181d28", outline="#4a5568", width=1.5)
            self.canvas.create_text(bx, by, text="⌛", fill="#8a99ad", font=("Segoe UI Emoji", 10))
            self.canvas.create_text(75, by, text="Loading...", fill="#8a99ad", font=("Segoe UI", 9, "italic"))
        elif self.gui_state == "idle":
            self.canvas.create_oval(bx - br, by - br, bx + br, by + br, fill="#0f2b38", outline="#00e5ff", width=1.5)
            tri = [bx - 4, by - 7, bx + 7, by, bx - 4, by + 7]
            self.canvas.create_polygon(tri, fill="#00e5ff")
            self._draw_waveform_lines(58, by, color="#252b3d")
        elif self.gui_state in ("recording", "listening"):
            # Red/Green pulsating circle
            ring_color = "#00e676" if self.gui_state == "listening" else "#ff5252"
            fill_color = "#0a2e1d" if self.gui_state == "listening" else "#3d1418"
            self.canvas.create_oval(bx - br - 2, by - br - 2, bx + br + 2, by + br + 2, fill="", outline=ring_color, width=1)
            self.canvas.create_oval(bx - br, by - br, bx + br, by + br, fill=fill_color, outline=ring_color, width=1.5)
            # Stop square
            sq = 5
            self.canvas.create_rectangle(bx - sq, by - sq, bx + sq, by + sq, fill=ring_color, outline="")
            self._draw_waveform_lines(58, by, color=ring_color)
        elif self.gui_state in ("processing", "transcribing"):
            self.canvas.create_oval(bx - br, by - br, bx + br, by + br, fill="#33250f", outline="#ffb74d", width=1.5)
            self.canvas.create_text(bx, by - 1, text="...", fill="#ffb74d", font=("Consolas", 12, "bold"))
            self._draw_waveform_lines(58, by, color="#ffb74d")
        elif self.gui_state == "analyzing":
            self.canvas.create_oval(bx - br, by - br, bx + br, by + br, fill="#2b1442", outline="#bb86fc", width=1.5)
            self.canvas.create_text(bx, by, text="✦", fill="#bb86fc", font=("Segoe UI Emoji", 11, "bold"))
            self._draw_waveform_lines(58, by, color="#bb86fc")

        # Meeting Dashboard Button (📅 / 🎙️)
        self.canvas.create_rectangle(120, 14, 154, 36, fill="#1c2130", outline="#3b4259", width=1)
        self.canvas.create_text(137, 25, text="LIVE 🎙️", fill="#00e5ff", font=("Segoe UI", 7, "bold"))

        # Close ✕
        self.canvas.create_text(w - 12, 12, text="✕", fill="#5a607a", font=("Arial", 8, "bold"))

    def _draw_waveform_lines(self, start_x: int, center_y: int, color: str):
        x_coords = [start_x, start_x + 12, start_x + 24, start_x + 36]
        for i, x in enumerate(x_coords):
            lh = int(self.line_heights[i])
            y1 = center_y - lh // 2
            y2 = center_y + lh // 2
            self.canvas.create_line(x, y1, x, y2, fill=color, width=3.5, capstyle="round")

    def _draw_rounded_rect(self, x1, y1, x2, y2, radius=15, **kwargs):
        points = [
            x1 + radius, y1, x2 - radius, y1, x2, y1,
            x2, y1 + radius, x2, y2 - radius, x2, y2,
            x2 - radius, y2, x1 + radius, y2, x1, y2,
            x1, y2 - radius, x1, y1 + radius, x1, y1
        ]
        return self.canvas.create_polygon(points, smooth=True, **kwargs)

    def _start_animation(self):
        if not self.animation_running:
            self.animation_running = True
            self.root.after(40, self._animate)

    def _stop_animation(self):
        self.animation_running = False
        self.line_heights = [10, 10, 10, 10]

    def _animate(self):
        if not self.animation_running:
            return
        t = self.anim_frame * 0.25
        for i in range(4):
            freq = 1.6 + i * 0.2
            phase = i * math.pi / 2
            amp = 10
            self.line_heights[i] = 7 + amp + amp * math.sin(t * freq + phase)
        self.anim_frame += 1
        self.redraw()
        self.root.after(40, self._animate)


class MeetingAssistantWindow:
    """
    Persistent Live Meeting Assistant Panel:
    - Displays cumulative transcript in real-time.
    - Status indicators (Listening, Transcribing, Analyzing, Completed).
    - Audio source selection (Mic, System WASAPI Loopback, Both).
    - Pause threshold tuning.
    - Finish & AI analysis generation with Enter-to-submit protection.
    - Structured analysis & action items presentation tab/dialog.
    """

    def __init__(self, master: tk.Tk, manager: Any):
        self.master = master
        self.manager = manager
        self.window: Optional[tk.Toplevel] = None
        
        # State
        self.enter_to_submit_var = tk.BooleanVar(value=True)
        self.audio_source_var = tk.StringVar(value="both")
        self.pause_threshold_var = tk.DoubleVar(value=2.0)
        self.status_text_var = tk.StringVar(value="Ready to start live meeting")
        self.word_count_var = tk.StringVar(value="Words: 0 | Segments: 0")

    def show(self):
        if self.window and self.window.winfo_exists():
            self.window.deiconify()
            self.window.lift()
            return

        self.window = tk.Toplevel(self.master)
        self.window.title("Live Meeting Assistant & AI Intelligence")
        self.window.geometry("860x650")
        self.window.minsize(700, 500)
        self.window.configure(bg="#12141d")

        self._setup_ui()
        self._bind_events()

    def _setup_ui(self):
        win = self.window
        
        # Header banner
        header_frame = tk.Frame(win, bg="#1a1e2b", padx=16, pady=12)
        header_frame.pack(fill="x", side="top")

        title_label = tk.Label(
            header_frame,
            text="🎙️ Live Meeting Intelligence",
            font=("Segoe UI", 14, "bold"),
            bg="#1a1e2b",
            fg="#00e5ff"
        )
        title_label.pack(side="left")

        # Meeting Title entry
        self.title_entry = tk.Entry(
            header_frame,
            font=("Segoe UI", 11),
            bg="#252b3d",
            fg="#ffffff",
            insertbackground="#00e5ff",
            relief="flat",
            width=30
        )
        self.title_entry.insert(0, self.manager.meeting_title or "Website Launch Planning Meeting")
        self.title_entry.pack(side="left", padx=15)

        # Status badge
        self.status_badge = tk.Label(
            header_frame,
            textvariable=self.status_text_var,
            font=("Segoe UI", 9, "bold"),
            bg="#252b3d",
            fg="#00e676",
            padx=10,
            pady=4
        )
        self.status_badge.pack(side="right")

        # Configuration Bar
        config_frame = tk.Frame(win, bg="#161924", padx=16, pady=8)
        config_frame.pack(fill="x", side="top")

        # Audio source
        tk.Label(config_frame, text="Audio Source:", font=("Segoe UI", 9), bg="#161924", fg="#8a99ad").pack(side="left", padx=4)
        src_combo = ttk.Combobox(
            config_frame,
            textvariable=self.audio_source_var,
            values=["both", "mic", "system"],
            state="readonly",
            width=10
        )
        src_combo.pack(side="left", padx=4)
        src_combo.bind("<<ComboboxSelected>>", self._on_source_change)

        # Pause threshold
        tk.Label(config_frame, text="Pause (s):", font=("Segoe UI", 9), bg="#161924", fg="#8a99ad").pack(side="left", padx=(15, 4))
        pause_spin = ttk.Spinbox(
            config_frame,
            from_=0.8,
            to=5.0,
            increment=0.2,
            textvariable=self.pause_threshold_var,
            width=5,
            command=self._on_pause_threshold_change
        )
        pause_spin.pack(side="left", padx=4)
        pause_spin.bind("<Return>", lambda e: self._on_pause_threshold_change())

        # Word count & stats
        self.stats_label = tk.Label(
            config_frame,
            textvariable=self.word_count_var,
            font=("Segoe UI", 9),
            bg="#161924",
            fg="#8a99ad"
        )
        self.stats_label.pack(side="right", padx=6)

        # Notebook (Tabs: Transcript vs AI Results)
        self.notebook = ttk.Notebook(win)
        self.notebook.pack(fill="both", expand=True, padx=16, pady=10)

        # Tab 1: Live Transcript
        self.tab_transcript = tk.Frame(self.notebook, bg="#12141d")
        self.notebook.add(self.tab_transcript, text="  Live Transcript  ")

        # Multiline text field with scrollbar
        text_frame = tk.Frame(self.tab_transcript, bg="#12141d")
        text_frame.pack(fill="both", expand=True)

        self.scrollbar = tk.Scrollbar(text_frame)
        self.scrollbar.pack(side="right", fill="y")

        self.transcript_text = tk.Text(
            text_frame,
            font=("Segoe UI", 11),
            bg="#171a24",
            fg="#e0e6ed",
            insertbackground="#00e5ff",
            selectbackground="#2d3748",
            wrap="word",
            padx=12,
            pady=12,
            yscrollcommand=self.scrollbar.set
        )
        self.transcript_text.pack(side="left", fill="both", expand=True)
        self.scrollbar.config(command=self.transcript_text.yview)

        # Tab 2: AI Analysis & Action Items
        self.tab_analysis = tk.Frame(self.notebook, bg="#12141d")
        self.notebook.add(self.tab_analysis, text="  AI Meeting Analysis & Tasks  ")

        self.analysis_scroll = tk.Scrollbar(self.tab_analysis)
        self.analysis_scroll.pack(side="right", fill="y")

        self.analysis_text = tk.Text(
            self.tab_analysis,
            font=("Segoe UI", 10),
            bg="#171a24",
            fg="#e0e6ed",
            insertbackground="#00e5ff",
            selectbackground="#2d3748",
            wrap="word",
            padx=14,
            pady=14,
            yscrollcommand=self.analysis_scroll.set
        )
        self.analysis_text.pack(side="left", fill="both", expand=True)
        self.analysis_scroll.config(command=self.analysis_text.yview)

        # Bottom Control Bar
        bottom_frame = tk.Frame(win, bg="#1a1e2b", padx=16, pady=12)
        bottom_frame.pack(fill="x", side="bottom")

        # Start / Resume button
        self.btn_start = tk.Button(
            bottom_frame,
            text="▶ Start Live Meeting",
            font=("Segoe UI", 10, "bold"),
            bg="#0f5132",
            fg="#ffffff",
            activebackground="#146c43",
            activeforeground="#ffffff",
            relief="flat",
            padx=14,
            pady=6,
            command=self._on_start_clicked
        )
        self.btn_start.pack(side="left", padx=(0, 8))

        # Pause button
        self.btn_pause = tk.Button(
            bottom_frame,
            text="⏸ Pause",
            font=("Segoe UI", 10),
            bg="#3d3314",
            fg="#ffc107",
            activebackground="#54451c",
            activeforeground="#ffc107",
            relief="flat",
            padx=12,
            pady=6,
            command=self._on_pause_clicked,
            state="disabled"
        )
        self.btn_pause.pack(side="left", padx=4)

        # Finish & Submit button
        self.btn_finish = tk.Button(
            bottom_frame,
            text="⏹ Finish Meeting & Run AI Analysis",
            font=("Segoe UI", 10, "bold"),
            bg="#6f42c1",
            fg="#ffffff",
            activebackground="#59359a",
            activeforeground="#ffffff",
            relief="flat",
            padx=14,
            pady=6,
            command=self._on_finish_clicked,
            state="disabled"
        )
        self.btn_finish.pack(side="left", padx=8)

        # Enter-to-Submit toggle
        self.chk_enter = tk.Checkbutton(
            bottom_frame,
            text="Enter in Title to Submit",
            variable=self.enter_to_submit_var,
            bg="#1a1e2b",
            fg="#8a99ad",
            selectcolor="#252b3d",
            activebackground="#1a1e2b",
            activeforeground="#00e5ff",
            font=("Segoe UI", 8)
        )
        self.chk_enter.pack(side="left", padx=10)

        # Export & Copy buttons
        self.btn_copy = tk.Button(
            bottom_frame,
            text="📋 Copy",
            font=("Segoe UI", 9),
            bg="#252b3d",
            fg="#e0e6ed",
            relief="flat",
            padx=10,
            pady=4,
            command=self._on_copy_clicked
        )
        self.btn_copy.pack(side="right", padx=4)

        self.btn_export = tk.Button(
            bottom_frame,
            text="💾 Export",
            font=("Segoe UI", 9),
            bg="#252b3d",
            fg="#e0e6ed",
            relief="flat",
            padx=10,
            pady=4,
            command=self._on_export_clicked
        )
        self.btn_export.pack(side="right", padx=4)

    def _bind_events(self):
        # Enter key in Title Entry triggers finish if enabled
        self.title_entry.bind("<Return>", self._on_title_enter_pressed)
        # Ctrl+Enter anywhere in transcript submits
        self.transcript_text.bind("<Control-Return>", lambda e: self._on_finish_clicked())
        # Sync user edits back to manager
        self.transcript_text.bind("<KeyRelease>", self._on_text_edited)

    def _on_source_change(self, event=None):
        src = self.audio_source_var.get()
        logger.info(f"Audio source switched to: {src}")

    def _on_pause_threshold_change(self):
        try:
            val = float(self.pause_threshold_var.get())
            self.manager.audio_engine.set_pause_threshold(val)
            logger.info(f"Updated meeting pause threshold to {val}s")
        except Exception:
            pass

    def _on_title_enter_pressed(self, event):
        if self.enter_to_submit_var.get():
            self._on_finish_clicked()

    def _on_text_edited(self, event=None):
        text = self.transcript_text.get("1.0", tk.END).strip()
        self.manager.set_cumulative_transcript(text)
        self._update_stats(text)

    def _on_start_clicked(self):
        title = self.title_entry.get().strip() or "Live Meeting"
        source = self.audio_source_var.get()
        self.manager.start_live_meeting(title=title, source=source)
        self.btn_start.config(state="disabled")
        self.btn_pause.config(state="normal")
        self.btn_finish.config(state="normal")
        self.transcript_text.delete("1.0", tk.END)

    def _on_pause_clicked(self):
        if self.manager.audio_engine.is_capturing:
            self.manager.pause_live_meeting()
            self.btn_pause.config(text="▶ Resume")
        else:
            source = self.audio_source_var.get()
            self.manager.resume_live_meeting(source=source)
            self.btn_pause.config(text="⏸ Pause")

    def _on_finish_clicked(self):
        title = self.title_entry.get().strip() or "Live Meeting"
        text = self.transcript_text.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("Empty Transcript", "The meeting transcript is empty. Speak into the microphone or capture system audio first.")
            return

        self.btn_start.config(state="disabled")
        self.btn_pause.config(state="disabled")
        self.btn_finish.config(state="disabled")

        self.manager.finish_meeting_and_submit(custom_title=title, auto_submit=True)

    def _on_copy_clicked(self):
        current_tab = self.notebook.index(self.notebook.select())
        if current_tab == 0:
            text = self.transcript_text.get("1.0", tk.END).strip()
        else:
            text = self.analysis_text.get("1.0", tk.END).strip()

        if text:
            self.master.clipboard_clear()
            self.master.clipboard_append(text)
            messagebox.showinfo("Copied", "Text copied to clipboard!")

    def _on_export_clicked(self):
        text = self.transcript_text.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("Empty Transcript", "Nothing to export.")
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text File", "*.txt"), ("Markdown File", "*.md"), ("JSON File", "*.json")]
        )
        if path:
            try:
                if path.endswith(".json") and self.manager.last_analysis_result and self.manager.last_analysis_result.raw_response:
                    with open(path, "w", encoding="utf-8") as f:
                        json.dump(self.manager.last_analysis_result.raw_response, f, indent=2)
                else:
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(text)
                messagebox.showinfo("Saved", f"Exported successfully to:\n{path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save export: {e}")

    # UI Update Callbacks (called thread-safely via root.after)
    def update_state(self, state: str, detail: str):
        if not self.window or not self.window.winfo_exists():
            return

        self.status_text_var.set(detail)
        colors = {
            "listening": ("#00e676", "#0a2e1d"),
            "recording": ("#ff5252", "#3d1418"),
            "transcribing": ("#ffc107", "#3d3314"),
            "finalizing": ("#ff9800", "#3d2a0a"),
            "analyzing": ("#bb86fc", "#2b1442"),
            "completed": ("#00e676", "#0a2e1d"),
            "error": ("#ff5252", "#3d1418"),
            "idle": ("#8a99ad", "#252b3d"),
        }
        fg, bg = colors.get(state, ("#8a99ad", "#252b3d"))
        self.status_badge.config(fg=fg, bg=bg)

        if state in ("completed", "error"):
            self.btn_start.config(state="normal")
            self.btn_pause.config(state="disabled", text="⏸ Pause")
            self.btn_finish.config(state="disabled")

    def append_segment(self, segment_dict: Dict[str, Any], full_text: str):
        if not self.window or not self.window.winfo_exists():
            return

        # Replace text in text widget smoothly and scroll to end
        self.transcript_text.delete("1.0", tk.END)
        self.transcript_text.insert(tk.END, full_text)
        self.transcript_text.see(tk.END)
        self._update_stats(full_text)

    def display_analysis_result(self, result: Any):
        if not self.window or not self.window.winfo_exists():
            return

        self.notebook.select(1)  # Switch to Analysis tab
        self.analysis_text.delete("1.0", tk.END)

        out = []
        out.append("=" * 60)
        out.append(f"AI MEETING ANALYSIS REPORT: {result.title}")
        out.append("=" * 60 + "\n")

        out.append("📌 EXECUTIVE SUMMARY:")
        out.append(result.executive_summary or "No executive summary provided.")
        out.append("\n" + "-" * 60 + "\n")

        if result.discussion_points:
            out.append("💬 KEY DISCUSSION POINTS:")
            for p in result.discussion_points:
                out.append(f"  • {p}")
            out.append("\n" + "-" * 60 + "\n")

        if result.decisions:
            out.append("✅ DECISIONS MADE:")
            for d in result.decisions:
                out.append(f"  ✓ {d}")
            out.append("\n" + "-" * 60 + "\n")

        if result.risks:
            out.append("⚠️ POTENTIAL RISKS & CONCERNS:")
            for r in result.risks:
                out.append(f"  ⚠️ {r}")
            out.append("\n" + "-" * 60 + "\n")

        if result.unresolved_questions:
            out.append("❓ UNRESOLVED QUESTIONS:")
            for q in result.unresolved_questions:
                out.append(f"  ? {q}")
            out.append("\n" + "-" * 60 + "\n")

        if result.tasks:
            out.append("📋 EXTRACTED ACTION ITEMS:")
            for i, t in enumerate(result.tasks, 1):
                owner = t.get("owner") or "Unassigned"
                deadline = t.get("deadline") or "No deadline"
                priority = (t.get("priority") or "medium").upper()
                title = t.get("title") or t.get("description")
                out.append(f"  [{i}] {title}")
                out.append(f"      Assignee: {owner} | Priority: {priority} | Deadline: {deadline}")
                if t.get("evidence_quote"):
                    out.append(f"      Evidence: \"{t.get('evidence_quote')}\"")
                out.append("")
            out.append("-" * 60 + "\n")

        if result.follow_up_plan:
            plan = result.follow_up_plan
            out.append("📅 FOLLOW-UP PLAN:")
            if plan.get("immediate_actions"):
                out.append("  Immediate Actions (0-48h):")
                for item in plan["immediate_actions"]:
                    out.append(f"    - {item.get('title', item)}")
            if plan.get("short_term_actions"):
                out.append("  Short-Term Actions (1-2 weeks):")
                for item in plan["short_term_actions"]:
                    out.append(f"    - {item.get('title', item)}")
            if plan.get("recommended_agenda_next_meeting"):
                out.append("  Recommended Next Agenda:")
                for item in plan["recommended_agenda_next_meeting"]:
                    out.append(f"    • {item}")
            out.append("\n")

        formatted = "\n".join(out)
        self.analysis_text.insert(tk.END, formatted)

    def _update_stats(self, text: str):
        words = len(text.split()) if text else 0
        segs = len(self.manager.segments)
        self.word_count_var.set(f"Words: {words} | Segments: {segs}")
