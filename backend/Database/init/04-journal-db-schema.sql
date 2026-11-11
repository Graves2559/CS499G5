-- 04-journal-db-schema.sql
-- Schema for JournalEntryDatabaseAdapter (backend/Security/Database.py).
-- Mirrors EncryptedFile.py/File.py (StorageNode.py) fields: plaintext
-- metadata (name, entry_type, entry_num, is_favorite, date_modified) is kept
-- outside the ciphertext so the storage tree can sort/display entries
-- without decrypting anything -- only `cyphertext` (the actual journal text)
-- is ever encrypted. See KeyManager.encryptFile for the corresponding split.
--
-- A page is persisted as soon as it's created (e2e.create_page), not only
-- once encrypted -- cyphertext/key_version are therefore nullable, and
-- plaintext_data holds the actual (readable!) content until the user
-- chooses to encrypt it. Exactly one of cyphertext/plaintext_data is ever
-- set for a given row (enforced below) -- once encrypt() runs, cyphertext
-- is filled in and plaintext_data is cleared, moving the content from
-- readable to zero-knowledge-encrypted.
--
-- entry_id is a human-readable NATURAL key -- the entry's own full path
-- ("<parent folder's path>/<name>"), never a surrogate UUID. Browsing this
-- table (e.g. in pgAdmin) shows e.g. "Root/Continuity/Pages/2026-10-31"
-- directly, mirroring File._path()/__repr__ (StorageNode.py) exactly.
-- Computed and assigned by e2e.py/EncryptionManager.Encrypt BEFORE insert --
-- never DB-generated. Unique per user only (PRIMARY KEY includes username):
-- two different users' entries can share the same entry_id/path, since
-- every query here is already scoped by username -- unique usernames are what
-- keep different users' data apart, not globally unique paths.
--
-- parent_folder_id mirrors storage_folders.folder_id (the parent folder's
-- own path) -- see 05-storage-folders-schema.sql for the FK (added there,
-- once that table exists) and its ON UPDATE CASCADE behavior.

\c "indexDB"

CREATE TYPE entry_type AS ENUM ('D', 'W', 'M', 'Y');

-- The web app's files use the defaults for entry_type/entry_num (they are journal-specific).
CREATE TABLE index_entries (
    entry_id         TEXT NOT NULL,          -- natural key: "<parent folder path>/<name>"
    username         TEXT NOT NULL,
    key_version      INTEGER,                -- which KeyRecord (in keyrecord_db) wrapped the dataKey used to encrypt
                                              -- this -- NULL until encrypt() has actually run on this entry
    name             TEXT NOT NULL,          -- plaintext (date string); needed for tree placement/sorting without decryption
    entry_type       entry_type NOT NULL DEFAULT 'D',
    entry_num        INTEGER NOT NULL DEFAULT 0,
    is_favorite      BOOLEAN NOT NULL DEFAULT false,
    date_modified    TEXT NOT NULL,
    cyphertext       BYTEA,                  -- AES-GCM ciphertext (nonce + ciphertext + tag); the actual journal
                                              -- content -- the join of every File.ItemList item's content, each
                                              -- marked by its id ("(id): content", one per line -- see
                                              -- File.syncDataFromItems) before encryption, so individual item
                                              -- content is recoverable on decrypt. NULL until encrypted.
    plaintext_data   TEXT,                   -- The SAME "(id): content"-marked text as cyphertext above, but in
                                              -- the clear -- readable in the DB until the user runs encrypt.
                                              -- NULL once encrypted (content moves to cyphertext instead).
    item_list        TEXT,                   -- Deliberately PLAINTEXT (not encrypted): a JSON array of
                                              -- {id, position, timestamp} per item -- NEVER content, which is
                                              -- already embedded (marked by id) in cyphertext/plaintext_data
                                              -- above. See KeyManager.encryptFile/decryptFile and
                                              -- File.populateItemContentFromData.
    media_id         TEXT,                   -- _id of this entry's content in MongoDB (GridFS), for image/video/large
                                              -- content that lives outside Postgres. When set, cyphertext and
                                              -- plaintext_data are both NULL. See backend/Security/MediaStore.py.
    description      TEXT NOT NULL DEFAULT '',   -- user-written note shown in the Files browser
    content_type     TEXT,                    -- MIME type of the content held in MongoDB
    size_bytes       BIGINT,                  -- size of the content held in MongoDB
    parent_folder_id TEXT,                   -- FK added in 05-storage-folders-schema.sql (that table doesn't exist yet here)
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (username, entry_id),
    CHECK (num_nonnulls(cyphertext, plaintext_data, media_id) = 1)
);

-- KeyManager.rotateKey's re-encryption pass fetches "every entry for this
-- user" via getAll(username) -- index to keep that fast as entries grow.
CREATE INDEX idx_index_entries_user ON index_entries (username);

-- No two entries share a name (case-insensitive) inside the same folder.
CREATE UNIQUE INDEX uq_index_entries_name ON index_entries (username, COALESCE(parent_folder_id, ''), lower(name));
