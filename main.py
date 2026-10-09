import tkinter as tk
import threading
import pyttsx3
import numpy as np
import sounddevice as sd
import tempfile
import wave
import os
import time
import logging
from datetime import datetime
from faster_whisper import WhisperModel
from pynput import keyboard, mouse
import pyperclip
import pyautogui
import win32gui
import win32con
import ctypes

from GUI import (
    create_floating_window,
    start_animation,
    stop_animation,
    draw_idle,
    set_gui_state,
    is_point_in_assistant
)

# === LOGGING SETUP ===
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('voice_assistant.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# === CONFIG ===
CONFIG = {
    'AUDIO_RATE': 16000,
    'TTS_RATE': 180,
    'TTS_VOLUME': 0.9,
    'MAX_TOKENS': 150,
    'WHISPER_MODEL': os.environ.get('WHISPER_MODEL', 'base'),
    'SILENCE_THRESHOLD': 0.003,      # Audio amplitude considered silence
    'SILENCE_DURATION_SEC': 1.4,     # Seconds of silence after speech to auto-stop
}

# === GLOBAL VARIABLES ===
tts = None
whisper = None
is_recording = False
shift_key_down = False
temp_files = []
processing_lock = threading.Lock()
tts_lock = threading.Lock()

# Target application & cursor tracking
last_target_window = None
last_target_click_pos = None

# === TTS FUNCTIONS ===
def debug_tts():
    logger.info("=== TTS DEBUG START ===")
    try:
        test_tts = pyttsx3.init()
        voices = test_tts.getProperty('voices')
        test_tts.setProperty('rate', 150)
        test_tts.setProperty('volume', 1.0)
        if voices:
            test_tts.setProperty('voice', voices[0].id)
        test_tts.say("Voice check")
        test_tts.runAndWait()
        test_tts.stop()
        logger.info("=== TTS DEBUG PASSED ===")
        return True
    except Exception as e:
        logger.error(f"TTS DEBUG FAILED: {str(e)}")
        return False

def initialize_tts():
    global tts
    try:
        tts = pyttsx3.init()
        voices = tts.getProperty('voices')
        if voices:
            tts.setProperty('voice', voices[0].id)
        tts.setProperty('rate', CONFIG['TTS_RATE'])
        tts.setProperty('volume', CONFIG['TTS_VOLUME'])
        return True
    except Exception as e:
        logger.error(f"TTS initialization failed: {e}")
        return False

def speak_response(text):
    global tts
    try:
        if tts:
            tts.say(text)
            tts.runAndWait()
    except Exception as e:
        logger.error(f"TTS error: {e}")

def speak_async(text):
    global tts
    if tts:
        threading.Thread(target=lambda: speak_response(text), daemon=True).start()

# === TARGET WINDOW & CURSOR TRACKER ===
def on_mouse_click(x, y, button, pressed):
    """Track the user's active application and click position in chat boxes/editors"""
    global last_target_click_pos, last_target_window
    if pressed and button == mouse.Button.left:
        # If clicked outside our floating widget, remember this target spot!
        if not is_point_in_assistant(x, y):
            last_target_click_pos = (x, y)
            try:
                fg = win32gui.GetForegroundWindow()
                if fg:
                    last_target_window = fg
            except Exception:
                pass

def paste_to_target_chat(text):
    """Accurately re-focuses the chat box and pastes the transcribed text"""
    global last_target_window, last_target_click_pos
    logger.info(f"Targeting paste for: {text}")

    # 1. Bring previous target window to foreground
    if last_target_window and win32gui.IsWindow(last_target_window):
        try:
            # Grant permission via Alt keybd_event trick in Windows
            ctypes.windll.user32.keybd_event(0x12, 0, 0, 0)
            ctypes.windll.user32.keybd_event(0x12, 0, 2, 0)
            ctypes.windll.user32.SetForegroundWindow(last_target_window)
            win32gui.BringWindowToTop(last_target_window)
        except Exception as e:
            logger.debug(f"Focus window error: {e}")

    # 2. Re-click into the chat box position if known, to activate the blinking cursor
    if last_target_click_pos and not is_point_in_assistant(*last_target_click_pos):
        try:
            pyautogui.click(last_target_click_pos[0], last_target_click_pos[1])
            time.sleep(0.08)
        except Exception as e:
            logger.debug(f"Click restore error: {e}")

    # 3. Copy to clipboard
    pyperclip.copy(text)
    time.sleep(0.05)

    # 4. Reliable paste using keyboard controller with hold duration
    try:
        kb = keyboard.Controller()
        kb.press(keyboard.Key.ctrl)
        time.sleep(0.05)
        kb.press('v')
        time.sleep(0.05)
        kb.release('v')
        time.sleep(0.05)
        kb.release(keyboard.Key.ctrl)
        logger.info("Successfully pasted transcribed text into chat box.")
    except Exception as e:
        logger.error(f"Keyboard paste error: {e}")
        # Fallback to pyautogui
        pyautogui.hotkey('ctrl', 'v')

# === INITIALIZATION ===
def initialize_models():
    global tts, whisper
    try:
        logger.info("=== INITIALIZING MODELS ===")
        initialize_tts()
        logger.info(f"Initializing Whisper ({CONFIG['WHISPER_MODEL']})...")
        whisper = WhisperModel(CONFIG['WHISPER_MODEL'], compute_type="int8", device="cpu")
        logger.info("Whisper initialized successfully")
        logger.info("=== ALL MODELS INITIALIZED ===")

        set_gui_state("idle")
        speak_response("Voice assistant is ready!")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize models: {e}")
        return False

# === AUDIO FUNCTIONS ===
def toggle_recording():
    """Toggle recording on or off"""
    global is_recording, whisper
    if whisper is None:
        logger.warning("Whisper model is still loading...")
        speak_async("Please wait, model is loading.")
        return

    if is_recording:
        stop_recording()
    else:
        start_recording()

def start_recording():
    global is_recording, whisper
    if whisper is None:
        return

    with processing_lock:
        if is_recording:
            return
        is_recording = True

    logger.info("Starting recording...")
    set_gui_state("recording")

    def record_loop():
        global is_recording
        audio_data = []
        speech_detected = False
        silence_frame_count = 0
        silence_frames_threshold = int(CONFIG['AUDIO_RATE'] / 512 * CONFIG['SILENCE_DURATION_SEC'])

        def audio_callback(indata, frames, time_info, status):
            nonlocal speech_detected, silence_frame_count
            if not is_recording:
                return

            samples = indata[:, 0]
            audio_data.extend(samples)

            # Silence detection for auto-stop
            vol = np.mean(np.abs(samples))
            if vol > CONFIG['SILENCE_THRESHOLD']:
                speech_detected = True
                silence_frame_count = 0
            elif speech_detected:
                silence_frame_count += 1
                if silence_frame_count >= silence_frames_threshold:
                    logger.info("Silence detected after speech - auto-stopping...")
                    stop_recording()

        try:
            with sd.InputStream(
                samplerate=CONFIG['AUDIO_RATE'],
                channels=1,
                callback=audio_callback,
                dtype='float32',
                blocksize=512
            ):
                while is_recording:
                    time.sleep(0.02)

            logger.info("Recording stopped. Processing audio...")
            set_gui_state("processing")

            if audio_data and len(audio_data) > CONFIG['AUDIO_RATE'] * 0.2:
                audio_array = np.array(audio_data, dtype=np.float32)
                volume = np.mean(np.abs(audio_array))
                if volume > 0.001:
                    audio_int16 = (audio_array * 32767).astype(np.int16)
                    process_audio(audio_int16)
                else:
                    logger.warning("Audio too quiet")
                    speak_async("I couldn't hear you clearly.")
                    set_gui_state("idle")
            else:
                logger.warning("Recording too short")
                set_gui_state("idle")
        except Exception as e:
            logger.error(f"Recording error: {e}")
            set_gui_state("idle")

    threading.Thread(target=record_loop, daemon=True).start()

def stop_recording():
    global is_recording
    with processing_lock:
        if not is_recording:
            return
        is_recording = False
    logger.info("Stopping recording...")

def process_audio(audio_data):
    """Transcribes audio and pastes text directly into chat box"""
    global whisper
    try:
        if whisper is None:
            return

        logger.info("Processing audio...")
        temp_path = save_temp_audio(audio_data)
        segments, info = whisper.transcribe(
            temp_path,
            language="en",
            beam_size=1,
            best_of=1,
            temperature=0.0,
            vad_filter=True,
            word_timestamps=False
        )
        all_text = " ".join([segment.text.strip() for segment in segments]).strip()
        logger.info(f"Transcribed: {all_text}")
        cleanup_temp_file(temp_path)

        # Remove repeated sentences
        import re
        phrases = re.split(r'(?<=[.?!])\s+', all_text)
        seen = set()
        filtered_phrases = []
        for phrase in phrases:
            phrase_clean = phrase.strip().lower()
            if phrase_clean and phrase_clean not in seen:
                seen.add(phrase_clean)
                filtered_phrases.append(phrase.strip())
        filtered_text = " ".join(filtered_phrases)

        if filtered_text and len(filtered_text.split()) >= 1:
            logger.info(f"Final Text: {filtered_text}")
            paste_to_target_chat(filtered_text)
        else:
            logger.info("No clear speech detected.")
    except Exception as e:
        logger.error(f"Audio processing error: {e}")
    finally:
        set_gui_state("idle")

def save_temp_audio(audio, rate=None):
    if rate is None:
        rate = CONFIG['AUDIO_RATE']
    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    temp_files.append(temp.name)
    with wave.open(temp.name, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(audio.tobytes())
    return temp.name

def cleanup_temp_file(temp_path):
    try:
        if os.path.exists(temp_path):
            os.remove(temp_path)
            if temp_path in temp_files:
                temp_files.remove(temp_path)
    except Exception as e:
        logger.warning(f"Failed to clean up temp file: {e}")

# === KEY HANDLING ===
def on_key_press(key):
    global shift_key_down
    try:
        if key == keyboard.Key.shift_r:
            if not shift_key_down:
                shift_key_down = True
                logger.info("Right Shift toggled")
                toggle_recording()
    except Exception as e:
        logger.error(f"Key press error: {str(e)}")

def on_key_release(key):
    global shift_key_down
    try:
        if key == keyboard.Key.shift_r:
            shift_key_down = False
        elif key == keyboard.Key.esc:
            logger.info("Exiting...")
            cleanup_and_exit()
    except Exception as e:
        logger.error(f"Key release error: {str(e)}")

def cleanup_and_exit():
    global is_recording
    logger.info("Cleaning up...")
    is_recording = False
    for temp_file in temp_files:
        try:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        except:
            pass
    try:
        if tts:
            tts.stop()
    except:
        pass
    try:
        from GUI import floating_window
        if floating_window:
            floating_window.quit()
            floating_window.destroy()
    except:
        pass
    import sys
    sys.exit(0)

def main():
    logger.info("=== STARTING ENHANCED AI VOICE ASSISTANT ===")
    create_floating_window(cleanup_and_exit, toggle_recording)

    def init_background():
        # Start mouse click tracker to capture chat box positions
        mouse_listener = mouse.Listener(on_click=on_mouse_click)
        mouse_listener.daemon = True
        mouse_listener.start()

        # Initialize models
        if not initialize_models():
            cleanup_and_exit()

        # Keyboard hotkey listener
        kb_listener = keyboard.Listener(
            on_press=on_key_press,
            on_release=on_key_release,
            daemon=True
        )
        kb_listener.start()

    threading.Thread(target=init_background, daemon=True).start()

    try:
        from GUI import floating_window
        floating_window.mainloop()
    except KeyboardInterrupt:
        logger.info("Interrupted")
    except Exception as e:
        logger.error(f"GUI error: {str(e)}")
    finally:
        cleanup_and_exit()

if __name__ == "__main__":
    main()