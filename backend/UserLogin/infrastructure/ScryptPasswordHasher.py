'''
ScryptPasswordHasher.py

Implements the PasswordHasher port with scrypt from the standard library.
'''
import hashlib
import hmac
import os

_SCRYPT_N = 2 ** 14
_SCRYPT_R = 8
_SCRYPT_P = 1


class ScryptPasswordHasher:
    def hash(self, password: str) -> tuple:
        salt = os.urandom(16)
        return salt, self._digest(password, salt)

    def verify(self, password: str, salt: bytes, digest: bytes) -> bool:
        return hmac.compare_digest(self._digest(password, salt), digest)

    def _digest(self, password: str, salt: bytes) -> bytes:
        return hashlib.scrypt(password.encode("utf-8"), salt=salt, n=_SCRYPT_N, r=_SCRYPT_R, p=_SCRYPT_P)
