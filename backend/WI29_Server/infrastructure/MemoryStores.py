'''
MemoryStores.py

In-memory implementations of the SessionStore, AttemptLimiter and PendingLogins ports. State is per server
process (it is lost on restart, and not shared between several server processes).
'''
import secrets
import threading
import time
from typing import Callable, Dict, List, Optional, Tuple


class InMemorySessionStore:
    def __init__(self, ttlSeconds: int, clock: Callable[[], float] = time.time):
        self.ttlSeconds = ttlSeconds
        self.clock = clock
        self._sessions: Dict[str, Tuple[str, float]] = {}
        self._lock = threading.Lock()

    def create(self, username: str) -> str:
        token = secrets.token_urlsafe(32)
        with self._lock:
            self._sessions[token] = (username, self.clock() + self.ttlSeconds)
        return token

    def username(self, token: Optional[str]) -> Optional[str]:
        if not token:
            return None
        with self._lock:
            session = self._sessions.get(token)
            if session is None:
                return None
            if session[1] < self.clock():
                del self._sessions[token]
                return None
            return session[0]

    def delete(self, token: Optional[str]) -> None:
        with self._lock:
            self._sessions.pop(token, None)


class SlidingWindowLimiter:
    def __init__(self, maxAttempts: int, windowSeconds: int, maxKeys: int = 1000,
                 clock: Callable[[], float] = time.time):
        self.maxAttempts = maxAttempts
        self.windowSeconds = windowSeconds
        self.maxKeys = maxKeys
        self.clock = clock
        self._attempts: Dict[str, List[float]] = {}
        self._lock = threading.Lock()

    def blocked(self, key: str) -> bool:
        with self._lock:
            return len(self._recent(key)) >= self.maxAttempts

    def record(self, key: str) -> None:
        with self._lock:
            recent = self._recent(key)
            if recent or len(self._attempts) < self.maxKeys:  # bounds memory against many different keys
                self._attempts[key] = recent + [self.clock()]

    def reset(self, key: str) -> None:
        with self._lock:
            self._attempts.pop(key, None)

    def _recent(self, key: str) -> List[float]:
        now = self.clock()
        recent = [t for t in self._attempts.get(key, []) if now - t < self.windowSeconds]
        if recent:
            self._attempts[key] = recent
        else:
            self._attempts.pop(key, None)
        return recent


class InMemoryPendingLogins:
    def __init__(self, ttlSeconds: int, capacity: int = 1000, clock: Callable[[], float] = time.time):
        self.ttlSeconds = ttlSeconds
        self.capacity = capacity
        self.clock = clock
        self._pending: Dict[str, Tuple[str, str, float]] = {}
        self._lock = threading.Lock()

    def add(self, state: str, codeVerifier: str, redirectUri: str) -> bool:
        now = self.clock()
        with self._lock:
            self._pending = {s: v for s, v in self._pending.items() if v[2] > now}
            if len(self._pending) >= self.capacity:
                return False
            self._pending[state] = (codeVerifier, redirectUri, now + self.ttlSeconds)
            return True

    def pop(self, state: str) -> Optional[Tuple[str, str]]:
        with self._lock:
            pending = self._pending.pop(state, None)
        if pending is None or pending[2] < self.clock():
            return None
        return pending[0], pending[1]
