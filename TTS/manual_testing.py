import sys
import os

# Same path setup as your test file
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(REPO_ROOT, "backend", "FolderStructure_User"))

from StorageNode import File
from WI3 import Reader

f = File()
f.setData("Hello, this is a test.")

reader = Reader()
reader.read_file(f)

# read_file returns immediately and the audio plays on a background thread,
# so wait for it to finish or the script exits before you hear anything.
reader.thread.join()