'''
PostgresFileRepositories.py

Implements the FolderRepository and FileIndex ports in the indexDB Postgres database
(storage_folders and index_entries, see Database/init/04-*.sql and 05-*.sql). Only metadata lives here;
the file content is in MongoDB and linked by index_entries.media_id.

A short-lived connection per operation keeps these safe under FastAPI's thread pool.
'''
from typing import List, Optional

import psycopg
from psycopg.errors import ForeignKeyViolation, UniqueViolation

from CommonErrors.Errors import ConflictError, NotFoundError
from WI29_Server.domain.Files import FileEntry, Folder


class _Postgres:
    def __init__(self, conninfo: str):
        self.conninfo = conninfo

    def _connect(self):
        return psycopg.connect(self.conninfo, autocommit=True)

    def _nameTaken(self, table: str, idColumn: str, username: str, parentId: Optional[str], name: str,
                   exceptId: Optional[str]) -> bool:
        with self._connect() as conn:
            row = conn.execute(
                f"SELECT 1 FROM {table} WHERE username = %s AND parent_folder_id IS NOT DISTINCT FROM %s "
                f"AND lower(name) = lower(%s) AND {idColumn} IS DISTINCT FROM %s",
                (username, parentId, name, exceptId),
            ).fetchone()
        return row is not None


class PostgresFolderRepository(_Postgres):
    def ensureDefault(self, username: str, folder: Folder) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO storage_folders (folder_id, username, name, description) VALUES (%s, %s, %s, %s) "
                "ON CONFLICT (username, folder_id) DO NOTHING",
                (folder.id, username, folder.name, folder.description),
            )

    def list(self, username: str) -> List[Folder]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT folder_id, parent_folder_id, name, description FROM storage_folders WHERE username = %s",
                (username,),
            ).fetchall()
        return [Folder(*row) for row in rows]

    def find(self, username: str, folderId: str) -> Optional[Folder]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT folder_id, parent_folder_id, name, description FROM storage_folders "
                "WHERE username = %s AND folder_id = %s",
                (username, folderId),
            ).fetchone()
        return Folder(*row) if row else None

    def add(self, username: str, folder: Folder) -> None:
        with self._connect() as conn:
            try:
                conn.execute(
                    "INSERT INTO storage_folders (folder_id, username, name, parent_folder_id, description) "
                    "VALUES (%s, %s, %s, %s, %s)",
                    (folder.id, username, folder.name, folder.parentId, folder.description),
                )
            except UniqueViolation:
                raise ConflictError("duplicate")
            except ForeignKeyViolation:
                raise NotFoundError("parent folder")

    def update(self, username: str, folderId: str, name: str, description: str) -> None:
        with self._connect() as conn:
            try:
                conn.execute(
                    "UPDATE storage_folders SET name = %s, description = %s WHERE username = %s AND folder_id = %s",
                    (name, description, username, folderId),
                )
            except UniqueViolation:
                raise ConflictError("duplicate")

    def nameTaken(self, username: str, parentId: Optional[str], name: str, exceptId: Optional[str]) -> bool:
        return self._nameTaken("storage_folders", "folder_id", username, parentId, name, exceptId)


class PostgresFileIndex(_Postgres):
    _COLUMNS = ("entry_id, parent_folder_id, name, description, content_type, size_bytes, is_favorite, "
                "date_modified, media_id")

    def list(self, username: str) -> List[FileEntry]:
        with self._connect() as conn:
            rows = conn.execute(
                f"SELECT {self._COLUMNS} FROM index_entries WHERE username = %s", (username,)
            ).fetchall()
        return [FileEntry(*row) for row in rows]

    def find(self, username: str, entryId: str) -> Optional[FileEntry]:
        with self._connect() as conn:
            row = conn.execute(
                f"SELECT {self._COLUMNS} FROM index_entries WHERE username = %s AND entry_id = %s",
                (username, entryId),
            ).fetchone()
        return FileEntry(*row) if row else None

    def upsert(self, username: str, entry: FileEntry) -> None:
        with self._connect() as conn:
            try:
                conn.execute(
                    "INSERT INTO index_entries (entry_id, username, name, parent_folder_id, description, "
                    "media_id, content_type, size_bytes, date_modified) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) "
                    "ON CONFLICT (username, entry_id) DO UPDATE SET media_id = EXCLUDED.media_id, "
                    "content_type = EXCLUDED.content_type, size_bytes = EXCLUDED.size_bytes, "
                    "date_modified = EXCLUDED.date_modified",
                    (entry.id, username, entry.name, entry.parentId, entry.description, entry.mediaId,
                     entry.contentType, entry.size, entry.dateModified),
                )
            except UniqueViolation:
                raise ConflictError("duplicate")
            except ForeignKeyViolation:
                raise NotFoundError("parent folder")

    def update(self, username: str, entryId: str, name: str, description: str,
               favorite: Optional[bool], dateModified: Optional[str]) -> None:
        with self._connect() as conn:
            try:
                conn.execute(
                    "UPDATE index_entries SET name = %s, description = %s, "
                    "is_favorite = COALESCE(%s::boolean, is_favorite), date_modified = COALESCE(%s::text, date_modified) "
                    "WHERE username = %s AND entry_id = %s",
                    (name, description, favorite, dateModified, username, entryId),
                )
            except UniqueViolation:
                raise ConflictError("duplicate")

    def nameTaken(self, username: str, parentId: Optional[str], name: str, exceptId: Optional[str]) -> bool:
        return self._nameTaken("index_entries", "entry_id", username, parentId, name, exceptId)
