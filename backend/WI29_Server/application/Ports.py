'''
Ports.py

The interfaces the use cases depend on. The infrastructure layer implements them (Postgres, MongoDB, in-memory
stores); the application layer never imports an implementation. Tests use small in-memory fakes.
'''
from typing import Any, List, Optional, Protocol, Tuple

from WI29_Server.domain.Files import FileEntry, Folder


class Account(Protocol):
    def getUsername(self) -> str: ...

    def getEncryptChoice(self) -> bool: ...


class Accounts(Protocol):
    '''What the sign-in use cases need from the accounts system (implemented by UserLogin's UserManager).'''

    def checkNewAccount(self, username: str, email: str) -> None:
        '''Raises ValidationError / ConflictError when the username or email cannot be used.'''

    def registerUser(self, username: str, email: str, password: str) -> Account: ...

    def seedUser(self, username: str, email: str, password: str) -> None: ...

    def authenticateUser(self, identifier: str, password: str) -> Optional[Account]: ...

    def getUser(self, username: str) -> Optional[Account]: ...

    def setEncryptChoice(self, user: Account, encryptChoice: bool) -> None: ...

    # RQ5/RQ8: sets up (or replaces) a user's security-question answers; verifies a set of candidate answers
    # (vacuously true if the user has none configured).
    def setupSecurityQuestions(self, user: Account, questionAnswers: dict) -> None: ...

    def verifySecurityAnswers(self, user: Account, candidateAnswers: dict) -> bool: ...


class FolderRepository(Protocol):
    def ensureDefault(self, username: str, folder: Folder) -> None:
        '''Adds the folder if the user does not have one with this id yet.'''

    def list(self, username: str) -> List[Folder]: ...

    def find(self, username: str, folderId: str) -> Optional[Folder]: ...

    def add(self, username: str, folder: Folder) -> None:
        '''Raises ConflictError (duplicate id or name) or NotFoundError (parent folder missing).'''

    def update(self, username: str, folderId: str, name: str, description: str) -> None:
        '''Raises ConflictError on a duplicate name.'''

    def nameTaken(self, username: str, parentId: Optional[str], name: str, exceptId: Optional[str]) -> bool:
        '''Case-insensitive, among the folders directly inside parentId (None = top level).'''


class FileIndex(Protocol):
    def list(self, username: str) -> List[FileEntry]: ...

    def find(self, username: str, entryId: str) -> Optional[FileEntry]: ...

    def upsert(self, username: str, entry: FileEntry) -> None:
        '''Inserts the entry, or for an existing id replaces only its content fields (media id, type, size, date).
        Raises ConflictError (duplicate name) or NotFoundError (parent folder missing).'''

    def update(self, username: str, entryId: str, name: str, description: str,
               favorite: Optional[bool], dateModified: Optional[str]) -> None:
        '''favorite / dateModified of None mean "leave unchanged". Raises ConflictError on a duplicate name.'''

    def nameTaken(self, username: str, parentId: Optional[str], name: str, exceptId: Optional[str]) -> bool: ...


class ContentStore(Protocol):
    def put(self, username: str, entryId: str, content: bytes, contentType: str) -> str:
        '''Stores the bytes and returns their media id.'''

    def get(self, mediaId: str) -> bytes:
        '''Raises NotFoundError if the content is gone.'''

    def delete(self, mediaId: str) -> None: ...


class SessionStore(Protocol):
    def create(self, username: str) -> str:
        '''Returns a new unguessable session token.'''

    def username(self, token: Optional[str]) -> Optional[str]: ...

    def delete(self, token: Optional[str]) -> None: ...


class AttemptLimiter(Protocol):
    def blocked(self, key: str) -> bool: ...

    def record(self, key: str) -> None: ...

    def reset(self, key: str) -> None: ...


class SymmetricKeyVault(Protocol):
    '''What FileService/KeyService need from a user's zero-knowledge symmetric-key encryption (implemented
    structurally by Security's EncryptionManager -- Security.application.KeyRecord.KeyRecord satisfies the
    `Any` return types here, but this context never imports that class directly, only through this port).'''

    # Returns (keyVersion, ciphertext); keyVersion must be stored alongside the ciphertext.
    def encryptContent(self, username: str, symmetricKey: str, plaintext: bytes) -> Tuple[int, bytes]: ...

    # Raises CommonErrors.Errors.CorruptedDataError on a wrong symmetricKey or tampered/corrupted ciphertext.
    def decryptContent(self, username: str, symmetricKey: str, keyVersion: int, ciphertext: bytes) -> bytes: ...

    def rotateKey(self, username: str, symmetricKey: str) -> Any: ...

    # RQ4: must be requested and confirmed before any of the 3 reset cases below.
    def requestResetConfirmation(self, username: str) -> str: ...

    def changePassphrase(self, username: str, confirmationCode: str, oldPassphrase: str, newPassphrase: str) -> Any: ...

    def generateRecoveryCode(self, username: str, passphrase: str) -> str: ...

    def recoverWithRecoveryCode(self, username: str, confirmationCode: str, recoveryCode: str, newPassphrase: str) -> Any: ...

    # Caller must delete every one of this user's encrypted files BEFORE calling this.
    def wipeAndReprovision(self, username: str, confirmationCode: str, newPassphrase: str) -> Tuple[Any, str]: ...
