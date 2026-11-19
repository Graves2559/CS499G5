# TTS
import os
import platform
import re
import shutil
import signal
import subprocess
import tempfile
import threading


from gtts import gTTS

MAX_CHARS = 400  # max characters sent to gTTS per request

# Voice selection: 
VOICES = {
    "1": ("English (US)", "en", "com"),
    "2": ("English (UK)", "en", "co.uk"),
    "3": ("English (Australia)", "en", "com.au"),
    "4": ("Spanish (Spain)", "es", "es"),
    "5": ("Spanish (Mexico)", "es", "com.mx"),
    "6": ("French (France)", "fr", "fr"),
}

def load_text(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def split_into_chunks(text, max_chars=MAX_CHARS):
    # Split text into chunks of at most max_chars, breaking at sentences.
    text = re.sub(r"\s+", " ", text).strip()
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks, current = [], ""

    for sentence in sentences:
        # A single sentence that is too long gets cut at word boundaries
        while len(sentence) > max_chars:
            cut = sentence.rfind(" ", 0, max_chars)
            if cut == -1:
                cut = max_chars
            piece, sentence = sentence[:cut], sentence[cut:].strip()
            if current:
                chunks.append(current)
                current = ""
            chunks.append(piece)

        if not sentence:
            continue

        if len(current) + len(sentence) + 1 <= max_chars:
            current = f"{current} {sentence}".strip()
        else:
            if current:
                chunks.append(current)
            current = sentence

    if current:
        chunks.append(current)
    return chunks


def player_command(path):
    # Return the command that plays an MP3 on this platform, or None.
    if platform.system() == "Darwin":
        return ["afplay", path]
    players = (
        ("mpg123", ["-q"]),
        ("ffplay", ["-nodisp", "-autoexit", "-loglevel", "quiet"]),
    )
    for name, args in players:
        if shutil.which(name):
            return [name, *args, path]
    return None


class Reader:
    def __init__(self):
        self.voice = VOICES["1"]
        self.proc = None
        self.thread = None
        self.stop_flag = threading.Event()
        self.paused = False

    #  controls 
    def start(self, text):
        self.stop()
        self.stop_flag = threading.Event()  # fresh flag for this run
        self.thread = threading.Thread(
            target=self._run, args=(text, self.voice, self.stop_flag), daemon=True
        )
        self.thread.start()

    def stop(self):
        self.stop_flag.set()
        if self.proc and self.proc.poll() is None:
            if self.paused and hasattr(signal, "SIGCONT"):
                os.kill(self.proc.pid, signal.SIGCONT)
            self.proc.terminate()
        self.paused = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=3)

    def toggle_pause(self):
        if not self.proc or self.proc.poll() is not None:
            print("Nothing is playing.")
            return
        if not hasattr(signal, "SIGSTOP"):
            print("Pause isn't supported on this platform. Use stop instead.")
            return
        if self.paused:
            os.kill(self.proc.pid, signal.SIGCONT)
            self.paused = False
            print("Resumed.")
        else:
            os.kill(self.proc.pid, signal.SIGSTOP)
            self.paused = True
            print("Paused.")

    # ---- background playback -------------------------------------------
    def _run(self, text, voice, stop_flag):
        label, lang, tld = voice
        chunks = split_into_chunks(text)
        print(f"Reading {len(chunks)} chunk(s) with voice: {label}")

        with tempfile.TemporaryDirectory() as tmp:
            for i, chunk in enumerate(chunks, 1):
                if stop_flag.is_set():
                    break
                path = os.path.join(tmp, f"chunk_{i}.mp3")
                try:
                    gTTS(text=chunk, lang=lang, tld=tld).save(path)
                except Exception as e:  # no internet, rate limit, etc.
                    print(f"gTTS error (check your internet connection): {e}")
                    break
                if stop_flag.is_set():
                    break

                cmd = player_command(path)
                if cmd is None:
                    print("No audio player found. Install mpg123 or ffplay.")
                    break
                print(f"  [chunk {i}/{len(chunks)}] {chunk[:60]}...")
                self.proc = subprocess.Popen(cmd)
                self.proc.wait()

        print("Finished." if not stop_flag.is_set() else "Stopped.")


def choose_voice(reader):
    print("\nAvailable voices:")
    for key, (label, lang, tld) in VOICES.items():
        print(f"  {key}. {label}  (lang={lang}, tld={tld})")
    choice = input("Pick a voice number: ").strip()
    if choice in VOICES:
        reader.voice = VOICES[choice]
        print(f"Voice set to: {reader.voice[0]}")
    else:
        print("Invalid choice, keeping current voice.")


def main():
    reader = Reader()
    menu = """
TTS Document Reader
 1. Read a .txt file aloud
 2. Pause / resume
 3. Stop
 4. Choose voice
 5. Read OCR-extracted text (not implemented yet)
 6. About / limitations
 7. Quit
"""
    while True:
        print(menu)
        choice = input("> ").strip()

        if choice == "1":
            raw = input("Path to .txt file: ").strip().strip("'\"")
            path = os.path.expanduser(raw.replace("\\ ", " "))
            try:
                text = load_text(path)
            except OSError as e:
                print(f"Couldn't open file: {e}")
                continue
            if not text.strip():
                print("That file is empty.")
                continue
            reader.start(text)
        elif choice == "2":
            reader.toggle_pause()
        elif choice == "3":
            reader.stop()
        elif choice == "4":
            choose_voice(reader)
        elif choice == "5":
            print("OCR isn't implemented yet. Once it is, pass its text output "
                  "to reader.start(ocr_text).")
        
        elif choice == "6":
            reader.stop()
            break
        else:
            print("Please enter a number from 1 to 7.")


if __name__ == "__main__":
    main()