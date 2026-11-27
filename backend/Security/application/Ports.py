'''
Ports.py

The interfaces the Security use cases depend on. Infrastructure (the actual cipher, the database) implements
them; the application layer never imports an implementation.
'''
from typing import List, Optional, Protocol

from Security.domain.KeyRecord import KeyRecord


class Cypher(Protocol):
    # AES-GCM encryption/decryption of arbitrary bytes (file content or a dataKey). `aad` is additional
    # authenticated data: checked but not encrypted. decrypt() raises CommonErrors.Errors.CorruptedDataError
    # on a wrong key or tampered data.
    def encrypt(self, plaintext: bytes, key: bytes, aad: Optional[bytes] = None) -> bytes: ...

    def decrypt(self, data: bytes, key: bytes, aad: Optional[bytes] = None) -> bytes: ...

    def generateSalt(self) -> bytes: ...

    # A fresh AES-256 dataKey: the key that actually encrypts file content.
    def generateDataKey(self) -> bytes: ...

    # Derives a wrapping key from a secret (the user's passphrase, or a one-time recovery code) and a salt,
    # via a slow, memory-hard KDF (Argon2id) so brute-forcing the passphrase is expensive.
    def deriveWrappingKey(self, secret: str, salt: bytes) -> bytes: ...

    # Same KDF, reused to hash security-question answers (and anything else that needs a slow, salted hash).
    def hashSecret(self, secret: str, salt: bytes) -> bytes: ...


class KeyRecordRepository(Protocol):
    def add(self, keyRecord: KeyRecord) -> None: ...

    def get(self, username: str, version: int) -> Optional[KeyRecord]: ...

    # The one row with status == ACTIVE for this user, or None if the user has no key yet.
    def getCurrent(self, username: str) -> Optional[KeyRecord]: ...

    def getAll(self, username: str) -> List[KeyRecord]: ...

    def update(self, keyRecord: KeyRecord) -> None: ...

    # Case 3 (wipe-and-reprovision): every previous key for this user is discarded.
    def deleteAll(self, username: str) -> None: ...


class ResetConfirmations(Protocol):
    # RQ4: generates (and remembers) the one-time code that must be confirmed before any symmetric-key
    # reset case runs. Returns the plaintext code; emailing it to the user's bound email is the caller's job.
    def request(self, username: str) -> str: ...

    # Raises CommonErrors.Errors.ValidationError when there is no pending code, it expired, or it is wrong.
    def confirm(self, username: str, code: str) -> None: ...
