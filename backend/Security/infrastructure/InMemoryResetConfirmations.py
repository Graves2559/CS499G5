'''
InMemoryResetConfirmations.py

Implements the ResetConfirmations port. State is per server process (it is lost on restart, and not shared
between several server processes) -- the same tradeoff as WI29_Server's InMemorySessionStore/
SlidingWindowLimiter.
'''
import threading
from typing import Dict

from Security.domain.PendingConfirmation import PendingConfirmation


class InMemoryResetConfirmations:
    def __init__(self):
        self._pending: Dict[str, PendingConfirmation] = {}
        self._lock = threading.Lock()

    def request(self, username: str) -> str:
        with self._lock:
            pending = self._pending.setdefault(username, PendingConfirmation())
        return pending.request()

    def confirm(self, username: str, code: str) -> None:
        with self._lock:
            pending = self._pending.get(username)
        if pending is None:
            pending = PendingConfirmation()  # confirm() on it raises "request a code first", same as missing
        pending.confirm(code)
