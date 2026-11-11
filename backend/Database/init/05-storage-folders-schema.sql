-- 05-storage-folders-schema.sql
-- Schema for StorageFolderDatabaseAdapter (backend/Security/Database.py).
-- Mirrors Folder (backend/Journaling/StorageNode.py): a self-referencing
-- tree of folders per user.
--
-- folder_id is a human-readable NATURAL key -- the folder's own full path
-- (e.g. "Root", "Root/Continuity", "Root/Continuity/Pages"), never a
-- surrogate UUID -- mirrors StorageNode._path()/__repr__ (StorageNode.py)
-- exactly, so browsing this table shows real, meaningful paths instead of
-- opaque IDs. Computed and assigned by e2e.py BEFORE insert -- never
-- DB-generated.
--
-- Unique per user only (PRIMARY KEY includes username): two different users
-- can both have a folder at "Root/Continuity/Pages" without conflict,
-- since every row (and every query) here is scoped by username -- unique
-- usernames are what keep different users' trees apart, not globally
-- unique names/paths.
--
-- parent_folder_id NULL means "this is a root folder" (StorageManager's own
-- Root folder has no parent, matching this exactly). ON UPDATE CASCADE:
-- renaming a folder changes its own folder_id (since the path changed),
-- and Postgres automatically repoints every direct child's parent_folder_id
-- to match -- e2e.py is still responsible for recomputing + persisting each
-- descendant's OWN folder_id/entry_id (the cascade only fixes the FK
-- pointer's value, not the text content of a child's own stored path).
--
-- Deliberately plaintext (no encryption) -- folder names/structure are
-- organizational metadata, not journal content, same tier as the plaintext
-- columns already on index_entries (name/entry_type/etc.).

\c "indexDB"

CREATE TABLE storage_folders (
    folder_id        TEXT NOT NULL,          -- natural key: "<parent folder path>/<name>", or just "<name>" for roots
    username         TEXT NOT NULL,
    name             TEXT NOT NULL,
    parent_folder_id TEXT,                   -- NULL = root
    is_locked        BOOLEAN NOT NULL DEFAULT false,
    description      TEXT NOT NULL DEFAULT '',   -- user-written note shown in the Files browser
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (username, folder_id),
    FOREIGN KEY (username, parent_folder_id) REFERENCES storage_folders(username, folder_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- StorageManager rebuilds a user's whole tree on startup -- index to keep
-- "every folder for this user" fast as the tree grows.
CREATE INDEX idx_storage_folders_user ON storage_folders (username);
CREATE INDEX idx_storage_folders_parent ON storage_folders (parent_folder_id);

-- No two folders share a name (case-insensitive) inside the same parent folder.
CREATE UNIQUE INDEX uq_storage_folders_name ON storage_folders (username, COALESCE(parent_folder_id, ''), lower(name));

-- index_entries.parent_folder_id was added as a bare TEXT column in
-- 04-journal-db-schema.sql (loaded before this file, so storage_folders
-- didn't exist yet to reference) -- attach the real FK constraint now.
-- ON DELETE CASCADE: deleting a folder deletes the entries filed under it,
-- mirroring StorageManager.Delete's existing recursive in-memory behavior.
-- ON UPDATE CASCADE: renaming a folder automatically repoints every entry
-- filed directly under it (same reasoning as the self-referencing FK above).
ALTER TABLE index_entries
    ADD CONSTRAINT fk_index_entries_parent_folder
    FOREIGN KEY (username, parent_folder_id) REFERENCES storage_folders(username, folder_id)
        ON DELETE CASCADE ON UPDATE CASCADE;

CREATE INDEX idx_index_entries_parent_folder ON index_entries (parent_folder_id);
