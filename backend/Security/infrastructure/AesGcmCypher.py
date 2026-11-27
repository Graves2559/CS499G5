'''
AesGcmCypher.py

Implements the Cypher port: AES-256-GCM for encryption, Argon2id for deriving a wrapping key from a
passphrase/recovery code. Mirrors the reference journaling program's Transformer/Cypher.py.
'''
import os

from argon2.low_level import Type, hash_secret_raw
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from CommonErrors.Errors import CorruptedDataError

NONCE_SIZE = 12   # 12 bytes for AES-GCM nonce
SALT_SIZE = 16    # 16 bytes for salt
KEY_SIZE = 32     # 32 bytes for an AES-256 key

# Argon2id parameters (RFC 9106-ish interactive settings): slow and memory-hard enough to make brute-forcing
# a wrong passphrase expensive, without being so slow it blocks ordinary requests.
_ARGON2_TIME_COST = 3
_ARGON2_MEMORY_COST = 65536  # 64 MiB, in KiB
_ARGON2_PARALLELISM = 4


class AesGcmCypher:
    # Encrypts: generates a fresh nonce, runs AES-GCM, and returns nonce + ciphertext + tag concatenated so
    # decrypt() only needs the key (and the same `aad`) to reverse it.
    def encrypt(self, plaintext: bytes, key: bytes, aad: bytes = None) -> bytes:
        nonce = os.urandom(NONCE_SIZE)
        return nonce + AESGCM(key).encrypt(nonce, plaintext, aad)

    # Raises CorruptedDataError on a wrong key or tampered/corrupted data (AES-GCM's authentication tag
    # fails to verify) -- this is the one place that distinguishes "wrong secret" from "bug", so it must
    # never leak which of the two actually happened.
    def decrypt(self, data: bytes, key: bytes, aad: bytes = None) -> bytes:
        nonce, body = data[:NONCE_SIZE], data[NONCE_SIZE:]
        try:
            return AESGCM(key).decrypt(nonce, body, aad)
        except InvalidTag:
            raise CorruptedDataError("Wrong passphrase/key, or the data was tampered with.")

    def generateSalt(self) -> bytes:
        return os.urandom(SALT_SIZE)

    def generateDataKey(self) -> bytes:
        return os.urandom(KEY_SIZE)

    # Derives a wrapping key from a secret and a salt via Argon2id -- deterministic (same secret + salt
    # always derives the same key), so the only way to get the right wrapping key back is to know `secret`.
    def deriveWrappingKey(self, secret: str, salt: bytes) -> bytes:
        return self._argon2id(secret, salt)

    def hashSecret(self, secret: str, salt: bytes) -> bytes:
        return self._argon2id(secret, salt)

    def _argon2id(self, secret: str, salt: bytes) -> bytes:
        return hash_secret_raw(
            secret=secret.encode("utf-8"),
            salt=salt,
            time_cost=_ARGON2_TIME_COST,
            memory_cost=_ARGON2_MEMORY_COST,
            parallelism=_ARGON2_PARALLELISM,
            hash_len=KEY_SIZE,
            type=Type.ID,  # Argon2id
        )
