-- 03-keyrecord-db-schema.sql
-- Schema for KeyRecordDatabaseAdapter (backend/Security/Database.py).
-- Mirrors KeyRecord.py exactly: the dataKey is never stored in plaintext --
-- only the wrapped (encrypted) form, under either the passphrase-derived
-- wrapping key (salt/encrypted_key) or the one-time recovery-code-derived
-- wrapping key (recovery_salt/recovery_encrypted_key). Both envelopes wrap
-- the SAME dataKey (see KeyManager.generateMasterKey).

\c keyrecord_db

CREATE TYPE key_status AS ENUM ('Current', 'Retired');

CREATE TABLE key_records (
    username               TEXT NOT NULL,
    key_version             INTEGER NOT NULL,
    encrypted_key           BYTEA NOT NULL,    -- wrapped dataKey (passphrase envelope)
    salt                    BYTEA NOT NULL,    -- salt used to derive the passphrase wrapping key
    status                  key_status NOT NULL DEFAULT 'Current',
    recovery_salt           BYTEA,             -- NULL until a recovery code has been generated (see KeyManager.generateMasterKey)
    recovery_encrypted_key  BYTEA,             -- wrapped dataKey (recovery-code envelope); NULL until generated, cleared again after one-time use
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    retired_at              TIMESTAMPTZ,
    PRIMARY KEY (username, key_version)
);

-- KeyManager.rotateKey/getKeyRecord look up "the current active key for this
-- user" frequently -- index to keep that fast as key history grows.
CREATE INDEX idx_key_records_user_status ON key_records (username, status);
