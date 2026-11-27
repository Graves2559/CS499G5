'''
User.py

Domain entity: user information within the journaling program. Knows nothing about databases or hashing
algorithms -- it only holds the (already hashed) password, which the application layer sets and verifies.
'''

# RQ: The email is required for account recovery and communication, and must be unique.
# RQ: The username cannot change after registration (every other table references it).
# RQ: The plaintext password is never stored; only a salted hash is kept.
# RQ: An email is bound to the account only after the user enters the verification code sent to it.
# RQ: A verification code expires after 10 minutes, and only a few wrong guesses are allowed per code.

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from CommonErrors.Errors import ValidationError

VERIFICATION_CODE_LENGTH = 6
VERIFICATION_CODE_LIFETIME = timedelta(minutes=10)
MAX_VERIFICATION_ATTEMPTS = 5


class User:
    def __init__(self, username: str, email: str):
        self.username = username
        self.email = email

        # Only the hash of the code is kept: (email to bind, code hash, expiry, wrong guesses so far).
        self._pendingEmail: Optional[str] = None
        self._pendingCodeHash = b""
        self._pendingExpiry: Optional[datetime] = None
        self._pendingAttempts = 0

        # Should not be stored inside the DB. Unlocks the encrypted data key.
        self.rawSymmetricKey = ""

        self._passwordSalt = b""
        self._passwordHash = b""

        # question -> {"salt": bytes, "answerHash": bytes}. Empty until the user opts in.
        self.securityQuestions: dict = {}
        self.encryptChoice = True

    def __repr__(self):
        return f"User(username={self.username!r}, email={self.email!r})"

    def getUsername(self) -> str:
        return self.username

    def getEmail(self) -> str:
        return self.email

    def setEmail(self, email: str):
        self.email = email

    def getPendingEmail(self) -> Optional[str]:
        return self._pendingEmail

    # Starts binding `email` and returns the code the caller must send to that address. Any earlier pending
    # code is discarded.
    def requestEmailVerification(self, email: str, now: Optional[datetime] = None) -> str:
        now = now or datetime.now(timezone.utc)
        code = "".join(secrets.choice("0123456789") for _ in range(VERIFICATION_CODE_LENGTH))
        self._pendingEmail = email
        self._pendingCodeHash = self._hashCode(code)
        self._pendingExpiry = now + VERIFICATION_CODE_LIFETIME
        self._pendingAttempts = 0
        return code

    # Binds the pending email when `code` is correct. Raises ValidationError when the code is wrong, expired,
    # or there is nothing to verify; the pending email is dropped once it expires or the guesses run out.
    def verifyEmail(self, code: str, now: Optional[datetime] = None) -> str:
        now = now or datetime.now(timezone.utc)
        if self._pendingEmail is None:
            raise ValidationError("No email is waiting to be verified. Request a verification code first.")
        if now > self._pendingExpiry:
            self._clearPendingEmail()
            raise ValidationError("The verification code has expired. Request a new one.")
        if not hmac.compare_digest(self._hashCode((code or "").strip()), self._pendingCodeHash):
            self._pendingAttempts += 1
            if self._pendingAttempts >= MAX_VERIFICATION_ATTEMPTS:
                self._clearPendingEmail()
                raise ValidationError("Wrong verification code. Too many attempts; request a new code.")
            raise ValidationError("Wrong verification code.")
        self.email = self._pendingEmail
        self._clearPendingEmail()
        return self.email

    def _clearPendingEmail(self):
        self._pendingEmail = None
        self._pendingCodeHash = b""
        self._pendingExpiry = None
        self._pendingAttempts = 0

    @staticmethod
    def _hashCode(code: str) -> bytes:
        return hashlib.sha256(code.encode()).digest()

    def getEncryptChoice(self) -> bool:
        return self.encryptChoice

    def setEncryptChoice(self, encryptChoice: bool):
        self.encryptChoice = encryptChoice

    def setPrivateKey(self, phrase: str):
        self.rawSymmetricKey = phrase

    def getPrivateKey(self) -> str:
        return self.rawSymmetricKey

    def setPasswordHash(self, salt: bytes, passwordHash: bytes):
        self._passwordSalt = salt
        self._passwordHash = passwordHash

    def getPasswordHash(self) -> tuple:
        return self._passwordSalt, self._passwordHash

    def hasPassword(self) -> bool:
        return bool(self._passwordHash)

    def setSecurityAnswerHash(self, question: str, salt: bytes, answerHash: bytes):
        self.securityQuestions[question] = {"salt": salt, "answerHash": answerHash}

    def getSecurityQuestions(self) -> dict:
        return self.securityQuestions
