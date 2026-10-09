# 🎙️ STS - AI Voice Assistant & Speech-to-Text

An intelligent, real-time desktop voice assistant that transcribes your speech with high accuracy and pastes it directly into whatever chat box, editor, or browser you are currently using—hands-free.

Powered by [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (CTranslate2-optimized Whisper), offline TTS, and a lightweight, draggable floating desktop widget.

---

## ✨ Features

- **🎯 Direct Caret Pasting**: Keeps track of where your cursor was last clicked (ChatGPT, Slack, Discord, WhatsApp Web, Word, IDEs) and pastes your transcribed text directly into the active input field.
- **🖥️ Non-Intrusive Floating Widget**: Sleek, dark-themed pill window with animated audio wave visualizers that stays on top without stealing focus from your typing application (`WS_EX_NOACTIVATE`).
- **⏯️ One-Click Play & Stop**: Click the **Play (▶)** button to start recording, and **Stop (■)** to finish and paste.
- **🤫 Hands-Free Auto-Stop on Silence**: Automatically detects when you stop talking (1.4 seconds of silence) and immediately pastes without needing to touch your mouse!
- **⌨️ Global Hotkey Toggle**: Tap <kbd>Right Shift</kbd> to toggle recording on and off hands-free; press <kbd>Esc</kbd> to exit.
- **⚡ Fast CPU Inference**: Uses `faster-whisper-base` for fast startup (<150 MB download) and responsive transcription on standard CPUs without requiring an NVIDIA GPU.
- **🗣️ Audio Feedback**: Built-in Text-to-Speech (TTS) via `pyttsx3` announces when models are ready or when audio is too quiet.

---

## 🚀 Quick Start

### 1. Prerequisites
- **Python**: 3.10 or higher
- **OS**: Windows 10 / 11

### 2. Installation

Clone the repository and install the dependencies:

```bash
git clone https://github.com/MRsanjuedit/STS.git
cd STS
pip install -r requirements.txt
```

> **Note**: Requirements include pre-built binary wheels for PyAV (`av`) to avoid needing Microsoft Visual C++ Build Tools.

### 3. Run the Assistant

```bash
python main.py
```

On first launch:
1. The assistant will check the local Text-to-Speech engine.
2. It will download the lightweight `faster-whisper-base` model (~140 MB) from Hugging Face and cache it locally.
3. The floating widget will appear at the top of your screen showing `⌛ Loading...`.
4. Once ready, the assistant will speak `"Voice assistant is ready!"` and the widget will switch to the cyan **Play (▶)** button.

---

## 🎮 How to Use

1. **Click where you want to type** (e.g. ChatGPT, Slack, WhatsApp Web, VS Code, or Notepad).
2. **Start speaking**:
   - Click the **Play (▶)** button on the floating widget, OR
   - Tap the <kbd>Right Shift</kbd> key.
3. **Finish speaking**:
   - **Hands-Free**: Simply stop talking for ~1.4 seconds—it will auto-detect silence, transcribe, and paste!
   - **Manual**: Click the **Stop (■)** button or tap <kbd>Right Shift</kbd> again.
4. Your speech is instantly transcribed and typed into your chat box.

### 🪟 Widget Controls
- **Drag Widget**: Click and drag anywhere on the pill widget to reposition it on your monitor.
- **Close Widget**: Click the small **✕** icon on the top right of the widget or press <kbd>Esc</kbd>.

---

## ⚙️ Configuration

You can customize assistant parameters at the top of [`main.py`](main.py):

| Setting | Default | Description |
|---|---|---|
| `WHISPER_MODEL` | `'base'` | Model size: `'tiny'`, `'base'`, `'small'`, `'medium'`, or `'large-v3'`. |
| `AUDIO_RATE` | `16000` | Audio sampling frequency (Hz). |
| `TTS_RATE` | `180` | Speed of the text-to-speech voice. |
| `TTS_VOLUME` | `0.9` | Volume of the voice feedback (0.0 to 1.0). |
| `SILENCE_DURATION_SEC` | `1.4` | Seconds of silence after speech before auto-stopping. |
| `SILENCE_THRESHOLD` | `0.003` | Audio volume threshold for silence detection. |

To use a different Whisper model (e.g. `small` for higher accuracy):
```powershell
$env:WHISPER_MODEL="small"; python main.py
```

---

## 📁 Project Structure

```
STS/
├── GUI.py              # Floating pill GUI, canvas rendering, and focus preservation logic
├── main.py             # Audio capture, faster-whisper transcription, hotkeys, and auto-paste
├── requirements.txt    # Pinned and compatible Python dependencies
├── .gitignore          # Ignores bytecode, temporary wav audio, and log files
└── README.md           # Project documentation
```

---

## 🛠️ Troubleshooting

- **Audio not pasting into browser chat?**
  Make sure you clicked into the chat box once before starting recording so the assistant knows where your cursor is located.
- **Model taking time to download?**
  The first run downloads the model from Hugging Face (~140 MB for `base`). Subsequent runs launch in 2 seconds from the local cache.
- **Audio too quiet?**
  Check your default microphone input in Windows Sound Settings and speak at a normal conversational volume.

---

## 📄 License

This project is open-source under the MIT License.
