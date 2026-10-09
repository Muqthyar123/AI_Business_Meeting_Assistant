import tkinter as tk
import threading
import time
import os
import sys
import logging
import argparse
from datetime import datetime
from typing import Optional, Dict, Any, List, Callable

# Windows GUI and system libraries
import pyperclip
import pyautogui

try:
    import win32gui
    import win32con
    import ctypes
except Exception:
    pass

try:
    import pyttsx3
except Exception:
    pass

from pynput import keyboard, mouse

from desktop.config import CONFIG
from desktop.meeting_manager import MeetingManager
from desktop.gui import MeetingAssistantWindow
from GUI import (
    create_floating_window,
    set_gui_state,
    is_point_in_assistant,
    floating_window
)

# === LOGGING SETUP ===
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('voice_assistant.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# === GLOBAL CONTROLLERS ===
meeting_manager: Optional[MeetingManager] = None
meeting_window: Optional[MeetingAssistantWindow] = None
tts_engine = None
tts_lock = threading.Lock()

# Target application & cursor tracking for Dictation pasting
last_target_window = None
last_target_click_pos = None
shift_key_down = False


# === TTS FUNCTIONS ===
def initialize_tts():
    global tts_engine
    if not CONFIG.ENABLE_TTS:
        return False
    try:
        tts_engine = pyttsx3.init()
        voices = tts_engine.getProperty('voices')
        if voices:
            tts_engine.setProperty('voice', voices[0].id)
        tts_engine.setProperty('rate', CONFIG.TTS_RATE)
        tts_engine.setProperty('volume', CONFIG.TTS_VOLUME)
        return True
    except Exception as e:
        logger.warning(f"TTS initialization failed (non-critical): {e}")
        return False


def speak_async(text: str):
    global tts_engine
    if not CONFIG.ENABLE_TTS or not tts_engine:
        return

    def _speak():
        with tts_lock:
            try:
                tts_engine.say(text)
                tts_engine.runAndWait()
            except Exception as e:
                logger.debug(f"TTS error: {e}")

    threading.Thread(target=_speak, daemon=True).start()


# === TARGET WINDOW & CURSOR TRACKER (FOR DICTATION) ===
def on_mouse_click(x, y, button, pressed):
    """Track the user's active application and click position in chat boxes/editors"""
    global last_target_click_pos, last_target_window
    if pressed and button == mouse.Button.left:
        # If clicked outside floating widget or meeting window, remember target
        if not is_point_in_assistant(x, y):
            last_target_click_pos = (x, y)
            try:
                fg = win32gui.GetForegroundWindow()
                if fg:
                    last_target_window = fg
            except Exception:
                pass


def paste_to_target_chat(text: str):
    """Accurately re-focuses the chat box and pastes the transcribed text"""
    global last_target_window, last_target_click_pos
    logger.info(f"Targeting paste for: '{text}'")

    if not text:
        return

    # 1. Bring previous target window to foreground
    if last_target_window:
        try:
            ctypes.windll.user32.keybd_event(0x12, 0, 0, 0)
            ctypes.windll.user32.keybd_event(0x12, 0, 2, 0)
            ctypes.windll.user32.SetForegroundWindow(last_target_window)
            win32gui.BringWindowToTop(last_target_window)
            time.sleep(0.05)
        except Exception as e:
            logger.debug(f"Focus window error: {e}")

    # 2. Re-click into the chat box position if known
    if last_target_click_pos and not is_point_in_assistant(*last_target_click_pos):
        try:
            pyautogui.click(last_target_click_pos[0], last_target_click_pos[1])
            time.sleep(0.08)
        except Exception as e:
            logger.debug(f"Click restore error: {e}")

    # 3. Copy to clipboard
    pyperclip.copy(text)
    time.sleep(0.05)

    # 4. Reliable paste using keyboard controller
    try:
        kb = keyboard.Controller()
        kb.press(keyboard.Key.ctrl)
        time.sleep(0.04)
        kb.press('v')
        time.sleep(0.04)
        kb.release('v')
        time.sleep(0.04)
        kb.release(keyboard.Key.ctrl)
        logger.info("Successfully pasted transcribed text into chat box.")
    except Exception as e:
        logger.error(f"Keyboard paste error: {e}")
        try:
            pyautogui.hotkey('ctrl', 'v')
        except Exception:
            pass


# === MEETING CALLBACKS ===
def on_manager_state_changed(state: str, detail: str):
    """Bridge MeetingManager state changes to GUI components"""
    try:
        set_gui_state(state)
        if meeting_window and floating_window:
            try:
                if floating_window.winfo_exists():
                    floating_window.after(0, lambda: meeting_window.update_state(state, detail))
            except Exception:
                pass
    except Exception:
        pass


def on_segment_added(segment_dict: dict, full_text: str):
    """Bridge new live meeting speech segment to GUI"""
    try:
        if meeting_window and floating_window:
            try:
                if floating_window.winfo_exists():
                    floating_window.after(0, lambda: meeting_window.append_segment(segment_dict, full_text))
            except Exception:
                pass
    except Exception:
        pass


def on_dictation_ready(text: str):
    """Handles transcribed dictation text by pasting into the active window"""
    paste_to_target_chat(text)


def on_analysis_complete(result):
    """Bridge AI meeting analysis results to GUI"""
    try:
        if meeting_window and floating_window:
            try:
                if floating_window.winfo_exists():
                    floating_window.after(0, lambda: meeting_window.display_analysis_result(result))
            except Exception:
                pass
    except Exception:
        pass


def on_manager_error(err_msg: str):
    logger.error(f"Meeting Assistant Error: {err_msg}")


# === UI ACTIONS ===
def toggle_dictation_recording():
    """Toggle dictation recording on or off"""
    if not meeting_manager:
        return

    if meeting_manager.audio_engine.is_capturing and meeting_manager.active_mode == "dictation":
        meeting_manager.stop_dictation()
    elif meeting_manager.current_state in ("idle", "error"):
        meeting_manager.start_dictation(source=CONFIG.DEFAULT_AUDIO_SOURCE)


def open_live_meeting_window():
    """Opens or focuses the dedicated Live Meeting Dashboard window"""
    global meeting_window
    if not meeting_window and floating_window:
        meeting_window = MeetingAssistantWindow(master=floating_window, manager=meeting_manager)
    if meeting_window:
        meeting_window.show()


# === KEYBOARD HANDLING ===
def on_key_press(key):
    global shift_key_down
    try:
        # Right Shift toggles general dictation mode
        if key == keyboard.Key.shift_r:
            if not shift_key_down:
                shift_key_down = True
                logger.info("Right Shift toggled dictation")
                toggle_dictation_recording()
    except Exception as e:
        logger.error(f"Key press error: {e}")


def on_key_release(key):
    global shift_key_down
    try:
        if key == keyboard.Key.shift_r:
            shift_key_down = False
        elif key == keyboard.Key.esc:
            logger.info("Escape pressed. Exiting...")
            cleanup_and_exit()
    except Exception as e:
        logger.error(f"Key release error: {e}")


def cleanup_and_exit():
    """Cleanly stops recording, joins threads, and exits"""
    global meeting_manager
    logger.info("Cleaning up and exiting application...")
    if meeting_manager:
        meeting_manager.shutdown()
    try:
        if tts_engine:
            tts_engine.stop()
    except Exception:
        pass
    try:
        from GUI import floating_window
        if floating_window:
            floating_window.quit()
            floating_window.destroy()
    except Exception:
        pass
    sys.exit(0)


def main():
    parser = argparse.ArgumentParser(description="AI Business Meeting Assistant - Live Voice & Meeting Intelligence")
    parser.add_argument("--meeting", action="store_true", help="Automatically open Live Meeting window on startup")
    parser.add_argument("--source", type=str, default="both", choices=["mic", "system", "both"], help="Audio source (mic, system, both)")
    parser.add_argument("--model", type=str, default=None, help="Whisper model (tiny, base, small, medium)")
    parser.add_argument("--backend-url", type=str, default=None, help="Backend API URL (default: http://127.0.0.1:8000)")
    args = parser.parse_args()

    if args.model:
        CONFIG.WHISPER_MODEL = args.model
    if args.backend_url:
        CONFIG.BACKEND_URL = args.backend_url
    if args.source:
        CONFIG.DEFAULT_AUDIO_SOURCE = args.source

    logger.info("=== STARTING AI BUSINESS MEETING ASSISTANT (LIVE & DICTATION) ===")
    
    # Create GUI floating pill
    root = create_floating_window(
        cleanup_and_exit=cleanup_and_exit,
        on_toggle_recording=toggle_dictation_recording,
        on_open_meeting=open_live_meeting_window
    )

    # Instantiate MeetingManager
    global meeting_manager, meeting_window
    meeting_manager = MeetingManager(
        config=CONFIG,
        on_state_changed=on_manager_state_changed,
        on_segment_added=on_segment_added,
        on_dictation_ready=on_dictation_ready,
        on_analysis_complete=on_analysis_complete,
        on_error=on_manager_error
    )

    meeting_window = MeetingAssistantWindow(master=root, manager=meeting_manager)

    def init_background():
        # Mouse listener for target window focus
        mouse_listener = mouse.Listener(on_click=on_mouse_click)
        mouse_listener.daemon = True
        mouse_listener.start()

        # Initialize TTS
        initialize_tts()

        # Initialize Whisper and Audio Engine
        if not meeting_manager.initialize():
            logger.error("Failed to initialize MeetingManager")
            set_gui_state("error")
        else:
            set_gui_state("idle")
            speak_async("Meeting Assistant is ready.")

        # Keyboard hotkey listener
        kb_listener = keyboard.Listener(
            on_press=on_key_press,
            on_release=on_key_release,
            daemon=True
        )
        kb_listener.start()

        # If --meeting flag passed, open meeting window
        if args.meeting and root.winfo_exists():
            root.after(200, open_live_meeting_window)

    threading.Thread(target=init_background, daemon=True).start()

    try:
        root.mainloop()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received.")
    except Exception as e:
        logger.error(f"GUI mainloop error: {e}")
    finally:
        cleanup_and_exit()


if __name__ == "__main__":
    main()
