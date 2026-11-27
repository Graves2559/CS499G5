'''
KeyManager.py

Core use case: wrapping/unwrapping the dataKey (the AES key that actually encrypts file content) inside a
KeyRecord's envelope(s), and rotating to a new KeyRecord. Pure logic -- no database, no persistence; the
facade (EncryptionManager) owns that. Mirrors the reference journaling program's KeyManager, minus the parts
that touch a File/journal database directly (content lives in WI29_Server here, reached only through its own
ports -- this context never encrypts/decrypts a "file", only bytes).
'''
from datetime import datetime, timezone
from typing import Optional, Tuple

from CommonErrors.Errors import CorruptedDataError
from Security.application.Ports import Cypher
from Security.domain.KeyRecord import KeyRecord, KeyStatus


class KeyManager:
    def __init__(self, cypher: Cypher):
        self.cypher = cypher

    # ===================== Wrapping/unwrapping the dataKey =====================
    # Envelope encryption: the dataKey is encrypted (wrapped) under a key derived from `secret`
    # (the user's passphrase, or a one-time recovery code). An attacker who only has the ciphertext content
    # cannot decrypt it without also knowing `secret`.
    def wrapDataKey(self, secret: str, dataKey: bytes) -> Tuple[bytes, bytes]:
        salt = self.cypher.generateSalt()
        wrappingKey = self.cypher.deriveWrappingKey(secret, salt)
        return salt, self.cypher.encrypt(dataKey, wrappingKey)

    # Raises CorruptedDataError on a wrong secret or a tampered/corrupted envelope.
    def unwrapDataKey(self, salt: bytes, encryptedKey: bytes, secret: str) -> bytes:
        wrappingKey = self.cypher.deriveWrappingKey(secret, salt)
        return self.cypher.decrypt(encryptedKey, wrappingKey)

    def unwrapWithPassphrase(self, keyRecord: KeyRecord, passphrase: str) -> bytes:
        return self.unwrapDataKey(keyRecord.salt, keyRecord.encryptedKey, passphrase)

    def unwrapWithRecoveryCode(self, keyRecord: KeyRecord, recoveryCode: str) -> bytes:
        if keyRecord.recoverySalt is None or keyRecord.recoveryEncryptedKey is None:
            raise CorruptedDataError("No recovery code was ever generated for this key.")
        return self.unwrapDataKey(keyRecord.recoverySalt, keyRecord.recoveryEncryptedKey, recoveryCode)

    # ===================== Generating/rotating a KeyRecord =====================
    # Generates a brand-new dataKey and its first (passphrase) envelope. `previous`, if given, is retired
    # (its status flips to RETIRED) -- version numbers are continuous across rotations.
    def generateKeyRecord(self, username: str, passphrase: str, previous: Optional[KeyRecord] = None) -> KeyRecord:
        dataKey = self.cypher.generateDataKey()
        salt, encryptedKey = self.wrapDataKey(passphrase, dataKey)
        version = 1 if previous is None else previous.version + 1
        if previous is not None:
            previous.status = KeyStatus.RETIRED
            previous.retiredAt = datetime.now(timezone.utc)
        return KeyRecord(version, salt, encryptedKey, username=username, createdAt=datetime.now(timezone.utc))

    # Re-wraps the SAME dataKey under a new passphrase (Case 1: the user still knows their current
    # passphrase). The key version and the wrapped file content are both unchanged.
    def rewrapWithNewPassphrase(self, keyRecord: KeyRecord, oldPassphrase: str, newPassphrase: str) -> KeyRecord:
        dataKey = self.unwrapWithPassphrase(keyRecord, oldPassphrase)
        keyRecord.salt, keyRecord.encryptedKey = self.wrapDataKey(newPassphrase, dataKey)
        return keyRecord

    # Re-wraps the SAME dataKey under a new passphrase using the recovery code instead (Case 2: the
    # passphrase is lost). One-time use: the caller must invalidate the recovery envelope after this.
    def rewrapWithRecoveryCode(self, keyRecord: KeyRecord, recoveryCode: str, newPassphrase: str) -> KeyRecord:
        dataKey = self.unwrapWithRecoveryCode(keyRecord, recoveryCode)
        keyRecord.salt, keyRecord.encryptedKey = self.wrapDataKey(newPassphrase, dataKey)
        keyRecord.recoverySalt = None
        keyRecord.recoveryEncryptedKey = None
        return keyRecord

    # Generates a brand-new, high-entropy one-time recovery code and adds its envelope to an existing
    # KeyRecord (wrapping the SAME dataKey as the passphrase envelope). Returns the plaintext code, which
    # must be shown to the user exactly once and never logged or stored.
    def attachRecoveryCode(self, keyRecord: KeyRecord, passphrase: str, recoveryCode: str) -> KeyRecord:
        dataKey = self.unwrapWithPassphrase(keyRecord, passphrase)
        keyRecord.recoverySalt, keyRecord.recoveryEncryptedKey = self.wrapDataKey(recoveryCode, dataKey)
        return keyRecord
