import sys
import os
import unittest
from unittest.mock import patch, MagicMock


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

sys.path.append(os.path.join(REPO_ROOT, "backend", "FolderStructure_User"))  # <- full folder name here

from StorageNode import File
from WI3 import Reader


class TestReadFile(unittest.TestCase):

    def make_file(self, text):
        f = File()
        f.setData(text)
        
        return f

    # --- Does read_file pass getData()'s string to start()? ---
    def test_read_file_sends_text_to_start(self):
        reader = Reader()
        f = self.make_file("Hello, this is a test.")

        with patch.object(reader, "start") as mock_start:
            reader.read_file(f)

        mock_start.assert_called_once_with("Hello, this is a test.")

    # --- Empty file: nothing should be spoken ---
    def test_empty_file_does_not_start(self):
        reader = Reader()
        f = self.make_file("")

        with patch.object(reader, "start") as mock_start:
            reader.read_file(f)

        mock_start.assert_not_called()

    # --- Whitespace-only file: also nothing to speak ---
    def test_whitespace_file_does_not_start(self):
        reader = Reader()
        f = self.make_file("   \n  ")

        with patch.object(reader, "start") as mock_start:
            reader.read_file(f)

        mock_start.assert_not_called()

    # --- Full pipeline: File -> getData -> start -> gTTS, with audio faked ---
    @patch("WI3.subprocess.Popen")
    @patch("WI3.player_command", return_value=["fake-player"])
    @patch("WI3.gTTS")
    def test_text_reaches_gtts(self, mock_gtts, mock_player, mock_popen):
        reader = Reader()
        f = self.make_file("Hello, this is a test.")

        reader.read_file(f)
        reader.thread.join(timeout=5)   # wait for the background thread

        mock_gtts.assert_called_once_with(
            text="Hello, this is a test.", lang="en", tld="com"
        )
        mock_gtts.return_value.save.assert_called_once()
        mock_popen.assert_called_once()  # "played" the audio


if __name__ == "__main__":
    unittest.main()