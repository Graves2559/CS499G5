'''
KeyRecordDatabaseAdapter.py

Implements the KeyRecordRepository port: stores KeyRecord information in the keyrecord_db Postgres database
(key_records table, see Database/init/03-keyrecord-db-schema.sql).
'''
from typing import List, Optional

import psycopg

from Security.domain.KeyRecord import KeyRecord, KeyStatus

_COLUMNS = ("username, key_version, encrypted_key, salt, status, recovery_salt, recovery_encrypted_key, "
            "created_at, retired_at")


def _rowToKeyRecord(row) -> KeyRecord:
    (username, version, encryptedKey, salt, status, recoverySalt, recoveryEncryptedKey, createdAt, retiredAt) = row
    return KeyRecord(
        version=version, salt=bytes(salt), encryptedKey=bytes(encryptedKey), username=username,
        status=KeyStatus(status), createdAt=createdAt, retiredAt=retiredAt,
        recoverySalt=bytes(recoverySalt) if recoverySalt is not None else None,
        recoveryEncryptedKey=bytes(recoveryEncryptedKey) if recoveryEncryptedKey is not None else None,
    )


class KeyRecordDatabaseAdapter:
    def __init__(self, connectionString: str):
        self.connectionString = connectionString
        self._conn = None

    # autocommit: every statement takes effect immediately.
    def connect(self):
        if self._conn is None or self._conn.closed:
            self._conn = psycopg.connect(self.connectionString, autocommit=True)
        return self._conn

    def disconnect(self):
        if self._conn is not None and not self._conn.closed:
            self._conn.close()

    def add(self, keyRecord: KeyRecord) -> None:
        self.connect().execute(
            f"INSERT INTO key_records ({_COLUMNS}) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (keyRecord.username, keyRecord.version, keyRecord.encryptedKey, keyRecord.salt,
             keyRecord.status.value, keyRecord.recoverySalt, keyRecord.recoveryEncryptedKey,
             keyRecord.createdAt, keyRecord.retiredAt),
        )

    def get(self, username: str, version: int) -> Optional[KeyRecord]:
        row = self.connect().execute(
            f"SELECT {_COLUMNS} FROM key_records WHERE username = %s AND key_version = %s", (username, version),
        ).fetchone()
        return _rowToKeyRecord(row) if row is not None else None

    # At most one row per user should ever have status = 'Current' by design.
    def getCurrent(self, username: str) -> Optional[KeyRecord]:
        row = self.connect().execute(
            f"SELECT {_COLUMNS} FROM key_records WHERE username = %s AND status = 'Current'", (username,),
        ).fetchone()
        return _rowToKeyRecord(row) if row is not None else None

    def getAll(self, username: str) -> List[KeyRecord]:
        rows = self.connect().execute(
            f"SELECT {_COLUMNS} FROM key_records WHERE username = %s ORDER BY key_version", (username,),
        ).fetchall()
        return [_rowToKeyRecord(row) for row in rows]

    def update(self, keyRecord: KeyRecord) -> None:
        self.connect().execute(
            "UPDATE key_records SET encrypted_key = %s, salt = %s, status = %s, recovery_salt = %s, "
            "recovery_encrypted_key = %s, retired_at = %s WHERE username = %s AND key_version = %s",
            (keyRecord.encryptedKey, keyRecord.salt, keyRecord.status.value, keyRecord.recoverySalt,
             keyRecord.recoveryEncryptedKey, keyRecord.retiredAt, keyRecord.username, keyRecord.version),
        )

    def deleteAll(self, username: str) -> None:
        self.connect().execute("DELETE FROM key_records WHERE username = %s", (username,))
