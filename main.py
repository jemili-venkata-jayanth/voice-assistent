import sys
import threading
import datetime
import os
import webbrowser

# --- AUDIO & SPEECH IMPORTS ---
import numpy as np
import sounddevice as sd
from scipy.io.wavfile import write
import speech_recognition as sr
import pyttsx3

# --- GUI IMPORTS (PyQt5) ---
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, 
    QTextEdit, QVBoxLayout, QHBoxLayout, QGraphicsColorizeEffect
)
from PyQt5.QtGui import QMovie, QColor
from PyQt5.QtCore import Qt, QTimer, QSize

# ==========================================
# 1. COLOR SCHEME & STYLING CONSTANTS (GREEN HUD)
# ==========================================
HUD_PRIMARY_GREEN = "#00FF41"  # CRT Matrix Green
HUD_GLOW_GREEN = "#11EE11"     # Highlight Glow Green

# Global CSS-style stylesheet for the PyQt window
HUD_STYLESHEET = """
    QWidget {
        background-color: #000305;
        color: #00FF41;
        font-family: 'Consolas', 'Courier New', monospace;
    }
    QLabel#ClockDisplay {
        color: #00FF41;
        background: transparent;
        font-size: 18pt;
        font-weight: bold;
    }
    QLabel#StatusIndicator {
        color: #00AA22;
        background: transparent;
        font-size: 10pt;
    }
    QPushButton#InitButton {
        background-color: #00FF41;
        color: #000305;
        border: 2px solid #00AA22;
        border-radius: 6px;
        font-size: 11pt;
        font-weight: bold;
        padding: 10px;
    }
    QPushButton#InitButton:hover {
        background-color: #33FF77;
    }
    QTextEdit#LogBox {
        background-color: #000508;
        border: 1px solid #00AA22;
        color: #00FF41;
        font-size: 10pt;
        border-radius: 4px;
        padding: 10px;
    }
"""

# ==========================================
# 2. VOICE SYNTHESIS INITIALIZATION (TTS)
# ==========================================
try:
    engine = pyttsx3.init()
    engine.setProperty('rate', 185)  # Set speaking speed
except Exception as e:
    print(f"Warning: Text-to-speech engine failed to initialize: {e}")

def speak(text, ui_callback=None):
    """
    Utility function to speak text out loud and optionally log it to the GUI text box.
    """
    if ui_callback:
        ui_callback(f"[J.A.R.V.I.S.]: {text}")
    try:
        engine.say(text)
        engine.runAndWait()
    except Exception:
        pass

# ==========================================
# 3. GRAPHICAL INTERFACE (GUI CLASS)
# ==========================================
class JarvisGreenHUD(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        # Configure Main Window Title and Dimensions
        self.setWindowTitle("J.A.R.V.I.S. Core Interface v0.9")
        self.setGeometry(150, 150, 900, 700)
        self.setStyleSheet(HUD_STYLESHEET)

        # Setup Layout Containers
        main_layout = QVBoxLayout()
        header_layout = QHBoxLayout()
        center_layout = QVBoxLayout()
        footer_layout = QHBoxLayout()

        # Header: Clock Display & System Status
        self.time_label = QLabel("SYSTEM BOOTING...", self)
        self.time_label.setObjectName("ClockDisplay")
        
        self.status_label = QLabel("SYSTEM IDLE", self)
        self.status_label.setObjectName("StatusIndicator")
        self.status_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        header_layout.addWidget(self.time_label)
        header_layout.addStretch()  # Pushes status text to the right
        header_layout.addWidget(self.status_label)
        main_layout.addLayout(header_layout)

        # Center Area: Animated Hologram GIF / Placeholder
        self.gif_container = QWidget(self)
        gif_vbox = QVBoxLayout(self.gif_container)
        
        self.gif_label = QLabel(self)
        self.gif_label.setAlignment(Qt.AlignCenter)
        self.gif_label.setMinimumSize(QSize(400, 400))
        
        # Load GIF if present and tint it translucent green
        gif_path = "jarvis_hologram.gif"
        if os.path.exists(gif_path):
            self.movie = QMovie(gif_path)
            self.gif_label.setMovie(self.movie)
            
            # Apply Green Hologram Color Effect
            colorize_effect = QGraphicsColorizeEffect()
            colorize_effect.setColor(QColor(0, 255, 65))
            colorize_effect.setStrength(0.9)
            self.gif_label.setGraphicsEffect(colorize_effect)
            self.movie.start()
        else:
            self.gif_label.setText("[HUD Hologram Active]")
            self.gif_label.setStyleSheet("color: #00FF41; font-size: 16pt;")

        gif_vbox.addWidget(self.gif_label, alignment=Qt.AlignCenter)
        center_layout.addWidget(self.gif_container)
        main_layout.addLayout(center_layout)

        # Footer Area: Log Terminal Box & Initialize Button
        self.log_box = QTextEdit(self)
        self.log_box.setObjectName("LogBox")
        self.log_box.setReadOnly(True)
        self.append_log("[SYSTEM]: Initialize core system to begin protocols.")
        
        self.start_btn = QPushButton("INITIALIZE INTERFACE", self)
        self.start_btn.setObjectName("InitButton")
        self.start_btn.setMinimumHeight(50)
        self.start_btn.clicked.connect(self.start_assistant_thread)

        footer_layout.addWidget(self.log_box, 3)   # Takes 3/4ths horizontal width
        footer_layout.addWidget(self.start_btn, 1)  # Takes 1/4th horizontal width
        main_layout.addLayout(footer_layout)

        self.setLayout(main_layout)

        # Timer to update clock every 1 second
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self.update_time_display)
        self.clock_timer.start(1000)

    # --- UI Helper Methods ---
    def update_time_display(self):
        """Updates top clock with real-time system clock."""
        now = datetime.datetime.now().strftime("%I:%M:%S %p")
        self.time_label.setText(now)

    def append_log(self, text):
        """Thread-safe logging method to write messages to log terminal."""
        QTimer.singleShot(0, lambda: self.log_box.append(f"{text}"))

    def set_status(self, text, color="#00AA22"):
        """Thread-safe status text updater."""
        QTimer.singleShot(0, lambda: self.status_label.setText(text.upper()))
        QTimer.singleShot(0, lambda: self.status_label.setStyleSheet(f"color: {color}; background: transparent;"))

    def start_assistant_thread(self):
        """Disables initialize button and launches assistant loop on background thread."""
        self.start_btn.setEnabled(False)
        self.start_btn.setText("SYSTEM ACTIVE")
        self.append_log("[>>>]: Boot Sequence Initialized...")
        self.set_status("INITIALIZING CORE...", HUD_GLOW_GREEN)
        
        # Run assistant logic in daemon thread to keep GUI smooth and responsive
        jarvis_thread = threading.Thread(target=self.run_jarvis_logic, daemon=True)
        jarvis_thread.start()

    # ==========================================
    # 4. MICROPHONE RECORDING (SOUNDDEVICE PIPELINE)
    # ==========================================
    def record_audio_clip(self, filename="temp_input.wav", duration=5, sample_rate=44100):
        """Records 5 seconds of microphone audio directly to temporary WAV file."""
        recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='int16')
        sd.wait()  # Wait until recording finishes
        write(filename, sample_rate, recording)

    # ==========================================
    # 5. CORE ASSISTANT LOGIC & COMMAND PARSER
    # ==========================================
    def run_jarvis_logic(self):
        speak("Core interface online. Voice audio pipeline ready.", self.append_log)
        recognizer = sr.Recognizer()
        
        while True:
            self.set_status("LISTENING (5s)...", HUD_PRIMARY_GREEN)
            self.append_log("[INPUT]: Listening for command...")
            
            # Step A: Record 5 seconds of audio
            temp_file = "temp_input.wav"
            self.record_audio_clip(temp_file, duration=5)
            
            self.set_status("PROCESSING...", HUD_GLOW_GREEN)
            
            # Step B: Pass recording to Google Speech Recognition
            try:
                with sr.AudioFile(temp_file) as source:
                    audio = recognizer.record(source)
                    command = recognizer.recognize_google(audio).lower()
                    self.append_log(f"[USER]: {command}")
                    
                    # Step C: Command Handlers
                    if "time" in command:
                        now = datetime.datetime.now().strftime("%I:%M %p")
                        speak(f"The time is {now}.", self.append_log)
                        
                    elif "open browser" in command or "open google" in command:
                        speak("Launching browser.", self.append_log)
                        webbrowser.open("https://google.com")
                        
                    elif "open notepad" in command:
                        speak("Opening notepad.", self.append_log)
                        os.system("notepad.exe")
                        
                    elif "shutdown" in command or "exit" in command:
                        speak("Powering down. Goodbye.", self.append_log)
                        QTimer.singleShot(1500, sys.exit)
                        break
                    else:
                        speak("Command not recognized.", self.append_log)

            except sr.UnknownValueError:
                self.append_log("[SYSTEM]: Silence or audio unclear.")
            except Exception as e:
                self.append_log(f"[ERR]: {str(e)}")
            
            # Cleanup temporary audio recording file
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception:
                    pass

# ==========================================
# 6. APPLICATION ENTRY POINT
# ==========================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    hud = JarvisGreenHUD()
    hud.show()
    sys.exit(app.exec_())
