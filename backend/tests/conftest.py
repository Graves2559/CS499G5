# Makes `CommonErrors`, `UserLogin` and `WI29_Server` importable no matter which folder pytest is started from.
import sys
from pathlib import Path

BACKEND = str(Path(__file__).resolve().parent.parent)
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)
