'''
PendingConfirmation.py

Domain value: a short-lived, single-use confirmation code. Used for RQ4 ("before resetting any symmetric
key, the system must require explicit confirmation from the bound email") -- Security only generates and
checks the code itself; sending it to the user's bound email is the caller's job, since the email address
belongs to UserLogin, not here.

Deliberately the same shape as UserLogin's email-verification code (hash only, expiry, limited attempts) --
see UserLogin/domain/User.py -- but kept as its own small type so this context never depends on that one.
'''
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from CommonErrors.Errors import ValidationError

CODE_LENGTH = 6
CODE_LIFETIME = timedelta(minutes=10)
MAX_ATTEMPTS = 5


class PendingConfirmation:
    def __init__(self):
        self._codeHash: Optional[bytes] = None
        self._expiry: Optional[datetime] = None
        self._attempts = 0

    # Returns the plaintext code to send to the user. Replaces any earlier pending code.
    def request(self, now: Optional[datetime] = None) -> str:
        now = now or datetime.now(timezone.utc)
        code = "".join(secrets.choice("0123456789") for _ in range(CODE_LENGTH))
        self._codeHash = self._hash(code)
        self._expiry = now + CODE_LIFETIME
        self._attempts = 0
        return code

    # Raises ValidationError when there is no pending code, it expired, or `code` is wrong. The pending code
    # is cleared on success, on expiry, and once the attempt limit is hit.
    def confirm(self, code: str, now: Optional[datetime] = None):
        now = now or datetime.now(timezone.utc)
        if self._codeHash is None:
            raise ValidationError("Request a confirmation code first.")
        if now > self._expiry:
            self.clear()
            raise ValidationError("The confirmation code has expired. Request a new one.")
        if not hmac.compare_digest(self._hash((code or "").strip()), self._codeHash):
            self._attempts += 1
            if self._attempts >= MAX_ATTEMPTS:
                self.clear()
                raise ValidationError("Wrong confirmation code. Too many attempts; request a new code.")
            raise ValidationError("Wrong confirmation code.")
        self.clear()

    def clear(self):
        self._codeHash = None
        self._expiry = None
        self._attempts = 0

    @staticmethod
    def _hash(code: str) -> bytes:
        return hashlib.sha256(code.encode()).digest()
