'''
FileService.py

Use cases for a user's folders and files. The rules live here (unique names, protected folders, favorites only
on files, size and type checks); where the data is stored is hidden behind the ports.
'''
from datetime import datetime, timezone
from typing import Callable, List, Optional, Tuple, Union

from CommonErrors.Errors import ConflictError, NotFoundError, PayloadTooLargeError, UnsupportedMediaError, ValidationError
from WI29_Server.application.Ports import ContentStore, FileIndex, FolderRepository
from WI29_Server.domain.Files import (
    DEFAULT_FOLDERS, MAX_DESCRIPTION_LENGTH, MAX_FILE_BYTES, PROTECTED_FOLDERS, FileEntry, Folder,
    detectContentType, requireValidId, requireValidName,
)

_NAME_TAKEN = "An item with this name already exists in this folder."


def _nowIso() -> str:
    return datetime.now(timezone.utc).isoformat()


class FileService:
    def __init__(self, folders: FolderRepository, files: FileIndex, content: ContentStore,
                 now: Callable[[], str] = _nowIso):
        self.folders = folders
        self.files = files
        self.content = content
        self.now = now

    def ensureDefaultFolders(self, username: str):
        for folderId, (name, description) in DEFAULT_FOLDERS.items():
            self.folders.ensureDefault(username, Folder(folderId, None, name, description))

    # Every user always has the default folders, so listing creates any that are missing.
    def listEntries(self, username: str) -> List[Union[Folder, FileEntry]]:
        self.ensureDefaultFolders(username)
        return [*self.folders.list(username), *self.files.list(username)]

    def createFolder(self, username: str, folderId: str, parentId: Optional[str], name: str, description: str):
        requireValidId(folderId)
        requireValidName(name)
        self._requireNameFree(username, parentId, name, exceptId=None)
        try:
            self.folders.add(username, Folder(folderId, parentId, name, description))
        except ConflictError:
            raise ConflictError("An item with this name or id already exists in this folder.")
        except NotFoundError:
            raise NotFoundError("Parent folder not found.")

    # Only files can be favorites (like the Favorites folder in StorageManager). Editing a file's name or
    # description updates its date modified; toggling a favorite does not.
    def updateEntry(self, username: str, entryId: str, name: Optional[str], description: Optional[str],
                    favorite: Optional[bool] = None):
        if name is not None:
            requireValidName(name)

        folder = self.folders.find(username, entryId)
        if folder is not None:
            if favorite is not None:
                raise ValidationError("Only files can be favorites.")
            if entryId in PROTECTED_FOLDERS:
                name = None  # the Input and Output folder names are fixed
            newName = name if name is not None else folder.name
            newDescription = description if description is not None else folder.description
            self._requireRenameFree(username, folder.parentId, folder.name, newName, entryId)
            try:
                self.folders.update(username, entryId, newName, newDescription)
            except ConflictError:
                raise ConflictError(_NAME_TAKEN)
            return

        entry = self.files.find(username, entryId)
        if entry is None:
            raise NotFoundError("Item not found.")
        newName = name if name is not None else entry.name
        newDescription = description if description is not None else entry.description
        self._requireRenameFree(username, entry.parentId, entry.name, newName, entryId)
        edited = newName != entry.name or newDescription != entry.description
        try:
            self.files.update(username, entryId, newName, newDescription, favorite,
                              self.now() if edited else None)
        except ConflictError:
            raise ConflictError(_NAME_TAKEN)

    # Creates the file, or replaces its content if this id already exists for the user. Returns (size, type).
    def putFile(self, username: str, entryId: str, parentId: str, name: str, description: str,
                content: bytes) -> Tuple[int, str]:
        requireValidId(entryId)
        if len(content) > MAX_FILE_BYTES:
            raise PayloadTooLargeError("File is larger than 25MB.")
        contentType = detectContentType(content)
        if contentType is None:
            raise UnsupportedMediaError("Only PNG, JPG, PDF and text files are supported.")
        requireValidName(name)

        existing = self.files.find(username, entryId)
        if existing is None:
            self._requireNameFree(username, parentId, name, exceptId=None)
        oldMediaId = existing.mediaId if existing else None

        # The two stores cannot share a transaction: content goes in first and is removed again if the index
        # write fails; the old content is only removed after the new index row is saved.
        newMediaId = self.content.put(username, entryId, content, contentType)
        entry = FileEntry(entryId, parentId, name, description[:MAX_DESCRIPTION_LENGTH], contentType,
                          len(content), False, self.now(), newMediaId)
        try:
            self.files.upsert(username, entry)
        except ConflictError:
            self.content.delete(newMediaId)
            raise ConflictError(_NAME_TAKEN)
        except NotFoundError:
            self.content.delete(newMediaId)
            raise NotFoundError("Parent folder not found.")
        except Exception:
            self.content.delete(newMediaId)
            raise
        if oldMediaId:
            self._deleteQuietly(oldMediaId)
        return len(content), contentType

    # Returns (content, content type, name).
    def getContent(self, username: str, entryId: str) -> Tuple[bytes, str, str]:
        entry = self.files.find(username, entryId)
        if entry is None or entry.mediaId is None:
            raise NotFoundError("File not found.")
        try:
            data = self.content.get(entry.mediaId)
        except NotFoundError:
            raise NotFoundError("File content not found.")
        return data, entry.contentType or "application/octet-stream", entry.name

    # Folders and files share one namespace inside a parent folder.
    def _requireNameFree(self, username: str, parentId: Optional[str], name: str, exceptId: Optional[str]):
        if self.folders.nameTaken(username, parentId, name, exceptId) or \
                self.files.nameTaken(username, parentId, name, exceptId):
            raise ConflictError(_NAME_TAKEN)

    def _requireRenameFree(self, username: str, parentId: Optional[str], oldName: str, newName: str, entryId: str):
        if newName.lower() != oldName.lower():
            self._requireNameFree(username, parentId, newName, exceptId=entryId)

    def _deleteQuietly(self, mediaId: str):
        try:
            self.content.delete(mediaId)
        except Exception:
            pass
