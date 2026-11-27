'''
EncryptionManager.py

Facade (use case) for a user's encryption: encrypting/decrypting content, rotating the symmetric key, and
the 3 cases for resetting it when the passphrase is lost (gated by RQ4's email confirmation code). Owns
persistence through KeyRecordRepository; the actual crypto decisions live in KeyManager, which this never
bypasses.

Security questions live in UserLogin (they gate account recovery, not encryption) -- verifying them, like
sending the RQ4 confirmation code to the user's bound email, is the caller's job (see
WI29_Server/application/KeyService.py, which composes this with UserLogin's Accounts port).
'''
import secrets
from typing import Tuple

from CommonErrors.Errors import CorruptedDataError, NotFoundError
from Security.application.KeyManager import KeyManager
from Security.application.Ports import Cypher, KeyRecordRepository, ResetConfirmations
from Security.domain.KeyRecord import KeyRecord

RECOVERY_CODE_BYTES = 16  # ~128 bits of entropy, matching the reference


class EncryptionManager:
    def __init__(self, keyRecords: KeyRecordRepository, cypher: Cypher, resetConfirmations: ResetConfirmations):
        self.keyRecords = keyRecords
        self.keyManager = KeyManager(cypher)
        self.resetConfirmations = resetConfirmations

    # ===================== SECTION 1: encrypting/decrypting content =====================
    # Creates the user's first KeyRecord if they don't have one yet.
    def ensureKey(self, username: str, passphrase: str) -> KeyRecord:
        current = self.keyRecords.getCurrent(username)
        if current is None:
            current = self.keyManager.generateKeyRecord(username, passphrase)
            self.keyRecords.add(current)
        return current

    # Returns (keyVersion, ciphertext); keyVersion must be stored alongside the ciphertext so decryptContent
    # knows which KeyRecord wrapped the dataKey that encrypted it.
    def encryptContent(self, username: str, passphrase: str, plaintext: bytes) -> Tuple[int, bytes]:
        keyRecord = self.ensureKey(username, passphrase)
        dataKey = self.keyManager.unwrapWithPassphrase(keyRecord, passphrase)
        return keyRecord.version, self.keyManager.cypher.encrypt(plaintext, dataKey)

    # Raises CorruptedDataError on a wrong passphrase or tampered/corrupted ciphertext (also raised if
    # keyVersion no longer exists, e.g. after Case 3's wipe).
    def decryptContent(self, username: str, passphrase: str, keyVersion: int, ciphertext: bytes) -> bytes:
        keyRecord = self.keyRecords.get(username, keyVersion)
        if keyRecord is None:
            raise CorruptedDataError("No key found for this content's key version.")
        dataKey = self.keyManager.unwrapWithPassphrase(keyRecord, passphrase)
        return self.keyManager.cypher.decrypt(ciphertext, dataKey)

    # ===================== SECTION 2: rotating the symmetric key =====================
    # RQ: every 180 days (NIST), or on demand. Generates a new KeyRecord and retires the old one; existing
    # content is NOT touched here -- the caller (WI29_Server, which owns that content) re-encrypts each item
    # by decrypting under the old keyVersion and re-encrypting through encryptContent, so the dataKey itself
    # never leaves this facade.
    def rotateKey(self, username: str, passphrase: str) -> KeyRecord:
        previous = self.keyRecords.getCurrent(username)
        newRecord = self.keyManager.generateKeyRecord(username, passphrase, previous)
        self.keyRecords.add(newRecord)
        if previous is not None:
            self.keyRecords.update(previous)
        return newRecord

    # ===================== SECTION 3: RQ4 confirmation + resetting the symmetric key =====================
    # RQ4: must be requested and confirmed before any of the 3 cases below. Returns the plaintext code --
    # emailing it to the user's bound email is the caller's job.
    def requestResetConfirmation(self, username: str) -> str:
        return self.resetConfirmations.request(username)

    def _requireConfirmed(self, username: str, confirmationCode: str):
        self.resetConfirmations.confirm(username, confirmationCode)

    def _requireCurrentKey(self, username: str) -> KeyRecord:
        keyRecord = self.keyRecords.getCurrent(username)
        if keyRecord is None:
            raise NotFoundError("No symmetric key exists yet for this user.")
        return keyRecord

    # Case 1: the user still knows their current passphrase. Re-wraps the SAME dataKey under the new
    # passphrase -- the key version (and every file encrypted under it) is unchanged.
    def changePassphrase(self, username: str, confirmationCode: str, oldPassphrase: str, newPassphrase: str) -> KeyRecord:
        self._requireConfirmed(username, confirmationCode)
        keyRecord = self._requireCurrentKey(username)
        self.keyManager.rewrapWithNewPassphrase(keyRecord, oldPassphrase, newPassphrase)
        self.keyRecords.update(keyRecord)
        return keyRecord

    # Not gated by RQ4: this only adds a backup envelope while the passphrase is still known, it does not
    # reset anything. Returns the plaintext recovery code -- show it to the user exactly once, never log or
    # store it.
    def generateRecoveryCode(self, username: str, passphrase: str) -> str:
        keyRecord = self._requireCurrentKey(username)
        recoveryCode = secrets.token_urlsafe(RECOVERY_CODE_BYTES)
        self.keyManager.attachRecoveryCode(keyRecord, passphrase, recoveryCode)
        self.keyRecords.update(keyRecord)
        return recoveryCode

    # Case 2: the passphrase is lost, but the one-time recovery code is available. One-time use: the
    # recovery envelope is invalidated as soon as this succeeds.
    def recoverWithRecoveryCode(self, username: str, confirmationCode: str, recoveryCode: str, newPassphrase: str) -> KeyRecord:
        self._requireConfirmed(username, confirmationCode)
        keyRecord = self._requireCurrentKey(username)
        self.keyManager.rewrapWithRecoveryCode(keyRecord, recoveryCode, newPassphrase)
        self.keyRecords.update(keyRecord)
        return keyRecord

    # Case 3 (last resort): both the passphrase and the recovery code are lost. Provisions a brand-new
    # dataKey (and a fresh recovery code) under the new passphrase. The caller MUST have already deleted
    # every one of this user's encrypted files before calling this -- their old dataKey becomes permanently
    # unrecoverable the moment this runs, so anything still wrapped under it is unrecoverable garbage.
    # Returns (the new KeyRecord, the new recovery code to show once).
    def wipeAndReprovision(self, username: str, confirmationCode: str, newPassphrase: str) -> Tuple[KeyRecord, str]:
        self._requireConfirmed(username, confirmationCode)
        self.keyRecords.deleteAll(username)
        newRecord = self.keyManager.generateKeyRecord(username, newPassphrase)
        self.keyRecords.add(newRecord)
        recoveryCode = secrets.token_urlsafe(RECOVERY_CODE_BYTES)
        self.keyManager.attachRecoveryCode(newRecord, newPassphrase, recoveryCode)
        self.keyRecords.update(newRecord)
        return newRecord, recoveryCode
