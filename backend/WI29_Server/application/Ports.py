'''
Ports.py

The interfaces the use cases depend on. The infrastructure layer implements them (Postgres, MongoDB, in-memory
stores, Google); the application layer never imports an implementation. Tests use small in-memory fakes.
'''
from typing import List, Optional, Protocol, Tuple

from WI29_Server.domain.Files import FileEntry, Folder
from WI29_Server.domain.Identity import ProviderProfile


class Account(Protocol):
    def getUsername(self) -> str: ...


class Accounts(Protocol):
    '''What the sign-in use cases need from the accounts system (implemented by UserLogin's UserManager).'''

    def checkNewAccount(self, username: str, email: str) -> None:
        '''Raises ValidationError / ConflictError when the username or email cannot be used.'''

    def registerUser(self, username: str, email: str, password: str) -> Account: ...

    def seedUser(self, username: str, email: str, password: str) -> None: ...

    def authenticateUser(self, identifier: str, password: str) -> Optional[Account]: ...

    def signInWithGoogle(self, googleID: str, email: str, name: str) -> str: ...


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


class PendingLogins(Protocol):
    def add(self, state: str, codeVerifier: str, redirectUri: str) -> bool:
        '''Remembers a started sign-in. Returns False if too many are pending.'''

    def pop(self, state: str) -> Optional[Tuple[str, str]]:
        '''Returns (codeVerifier, redirectUri) once, or None if unknown or expired.'''


class IdentityProvider(Protocol):
    @property
    def configured(self) -> bool: ...

    def authorizationUrl(self, redirectUri: str, state: str, codeChallenge: str) -> str:
        '''Raises ExternalServiceError if the provider cannot be reached.'''

    def fetchProfile(self, code: str, redirectUri: str, codeVerifier: str) -> ProviderProfile:
        '''Raises ExternalServiceError if the code cannot be exchanged.'''
