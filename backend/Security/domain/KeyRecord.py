'''
KeyRecord.py

Domain value: a user's wrapped (encrypted) dataKey and its metadata. Pure Python: no database, crypto
library or I/O. Mirrors the reference journaling program's KeyRecord (and backend/Database/init/
03-keyrecord-db-schema.sql here), but holds plain bytes instead of get/set methods.

RQ: The dataKey (the AES key that actually encrypts file content) is never stored in plaintext -- only the
wrapped (encrypted) form lives here, under either the passphrase-derived wrapping key (salt/encryptedKey) or
the one-time recovery-code-derived wrapping key (recoverySalt/recoveryEncryptedKey). Both envelopes wrap the
SAME dataKey.
'''
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class KeyStatus(Enum):
    ACTIVE = "Current"
    RETIRED = "Retired"


@dataclass
class KeyRecord:
    version: int
    salt: bytes
    encryptedKey: bytes
    username: str = ""
    status: KeyStatus = KeyStatus.ACTIVE
    createdAt: Optional[datetime] = None
    retiredAt: Optional[datetime] = None
    # The same dataKey is also wrapped under a one-time recovery code (an independent envelope, same
    # dataKey), so either the passphrase or the recovery code alone can unwrap it. None until a recovery
    # code has actually been generated for this key.
    recoverySalt: Optional[bytes] = None
    recoveryEncryptedKey: Optional[bytes] = None
