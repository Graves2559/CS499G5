'''
FileService.py

Use cases for a user's folders and files. The rules live here (unique names, protected folders, favorites only
on files, size and type checks); where the data is stored is hidden behind the ports.
'''
from datetime import datetime, timezone
from typing import Callable, List, Optional, Tuple, Union

from CommonErrors.Errors import ConflictError, NotFoundError, PayloadTooLargeError, UnsupportedMediaError, ValidationError
from WI29_Server.application.Ports import ContentStore, FileIndex, FolderRepository, SymmetricKeyVault
from WI29_Server.domain.Files import (
    DEFAULT_FOLDERS, MAX_DESCRIPTION_LENGTH, MAX_FILE_BYTES, PROTECTED_FOLDERS, FileEntry, Folder,
    detectContentType, requireValidId, requireValidName,
)

_NAME_TAKEN = "An item with this name already exists in this folder."
_NEEDS_PASSPHRASE = "Enter your passphrase to decrypt this file."


def _nowIso() -> str:
    return datetime.now(timezone.utc).isoformat()


class FileService:
    def __init__(self, folders: FolderRepository, files: FileIndex, content: ContentStore,
                 now: Callable[[], str] = _nowIso, vault: Optional[SymmetricKeyVault] = None):
        self.folders = folders
        self.files = files
        self.content = content
        self.now = now
        self.vault = vault

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
    # `symmetricKey`, when given, encrypts the content at rest (RQ: "Image & video encryption" setting) --
    # the dataKey and the passphrase itself never touch the database, only the ciphertext and the key
    # version that wrapped the dataKey used (see Security.application.EncryptionManager).
    def putFile(self, username: str, entryId: str, parentId: str, name: str, description: str,
                content: bytes, symmetricKey: Optional[str] = None) -> Tuple[int, str]:
        requireValidId(entryId)
        if len(content) > MAX_FILE_BYTES:
            raise PayloadTooLargeError("File is larger than 25MB.")
        contentType = detectContentType(content)  # decided from the plaintext bytes, before any encryption
        if contentType is None:
            raise UnsupportedMediaError("Only PNG, JPG, PDF and text files are supported.")
        requireValidName(name)

        existing = self.files.find(username, entryId)
        if existing is None:
            self._requireNameFree(username, parentId, name, exceptId=None)
        oldMediaId = existing.mediaId if existing else None

        size = len(content)
        keyVersion, toStore = self._encryptIfRequested(username, symmetricKey, content)

        # The two stores cannot share a transaction: content goes in first and is removed again if the index
        # write fails; the old content is only removed after the new index row is saved.
        newMediaId = self.content.put(username, entryId, toStore, contentType)
        entry = FileEntry(entryId, parentId, name, description[:MAX_DESCRIPTION_LENGTH], contentType,
                          size, False, self.now(), newMediaId, keyVersion)
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
        return size, contentType

    # Returns (content, content type, name). `symmetricKey` is required when the stored content is encrypted
    # (raises ValidationError if missing, CorruptedDataError on the wrong passphrase).
    def getContent(self, username: str, entryId: str, symmetricKey: Optional[str] = None) -> Tuple[bytes, str, str]:
        entry = self.files.find(username, entryId)
        if entry is None or entry.mediaId is None:
            raise NotFoundError("File not found.")
        try:
            data = self.content.get(entry.mediaId)
        except NotFoundError:
            raise NotFoundError("File content not found.")
        if entry.keyVersion is not None:
            if not symmetricKey:
                raise ValidationError(_NEEDS_PASSPHRASE)
            data = self.vault.decryptContent(username, symmetricKey, entry.keyVersion, data)
        return data, entry.contentType or "application/octet-stream", entry.name

    # RQ: every 180 days (NIST), or on demand -- generates a brand-new dataKey and re-encrypts every one of
    # this user's encrypted files under it. The passphrase itself is unchanged; see KeyService for changing
    # the passphrase instead (Case 1), which re-wraps the existing dataKey and never touches file content.
    def rotateEncryptionKey(self, username: str, symmetricKey: str):
        if self.vault is None:
            raise ValidationError("Encryption is not available.")
        self.vault.rotateKey(username, symmetricKey)
        for entry in self.files.list(username):
            if entry.keyVersion is None:
                continue
            ciphertext = self.content.get(entry.mediaId)
            plaintext = self.vault.decryptContent(username, symmetricKey, entry.keyVersion, ciphertext)
            newVersion, newCiphertext = self.vault.encryptContent(username, symmetricKey, plaintext)
            newMediaId = self.content.put(username, entry.id, newCiphertext, entry.contentType)
            self.files.upsert(username, FileEntry(entry.id, entry.parentId, entry.name, entry.description,
                                                   entry.contentType, entry.size, entry.favorite,
                                                   entry.dateModified, newMediaId, newVersion))
            self._deleteQuietly(entry.mediaId)

    def _encryptIfRequested(self, username: str, symmetricKey: Optional[str], content: bytes) -> Tuple[Optional[int], bytes]:
        if not symmetricKey:
            return None, content
        if self.vault is None:
            raise ValidationError("Encryption is not available.")
        return self.vault.encryptContent(username, symmetricKey, content)

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
