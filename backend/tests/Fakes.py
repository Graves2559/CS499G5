'''
Fakes.py

Small in-memory implementations of the ports, so the use cases can be tested without Postgres, MongoDB or Google.
'''
import itertools
from typing import Dict, List, Optional, Tuple

from CommonErrors.Errors import ConflictError, NotFoundError
from UserLogin.domain.User import User
from WI29_Server.domain.Files import FileEntry, Folder
from WI29_Server.domain.Identity import ProviderProfile


class FakeHasher:
    def __init__(self):
        self.verifyCalls = 0

    def hash(self, password: str) -> tuple:
        return b"salt", b"hash:" + password.encode()

    def verify(self, password: str, salt: bytes, digest: bytes) -> bool:
        self.verifyCalls += 1
        return digest == b"hash:" + password.encode()


class FakeUsers:
    def __init__(self):
        self.users: Dict[str, User] = {}
        self.googleIds: Dict[str, str] = {}

    def get(self, username):
        return self.users.get(username)

    def findUsername(self, identifier):
        key = identifier.lower()
        for user in self.users.values():
            if (user.getEmail().lower() if "@" in key else user.getUsername().lower()) == key:
                return user.getUsername()
        return None

    def findUsernameByGoogleID(self, googleID):
        return self.googleIds.get(googleID)

    def add(self, user, googleID=None):
        if self.findUsername(user.getUsername()) or self.findUsername(user.getEmail()):
            raise ConflictError("That username or email is already in use.")
        self.users[user.getUsername()] = user
        if googleID:
            self.googleIds[googleID] = user.getUsername()

    def update(self, username, email=None, encryptChoice=None):
        pass

    def updatePassword(self, user):
        self.users[user.getUsername()] = user

    def delete(self, username):
        self.users.pop(username, None)


class FakeFolders:
    def __init__(self):
        self.rows: Dict[Tuple[str, str], Folder] = {}

    def ensureDefault(self, username, folder):
        self.rows.setdefault((username, folder.id), folder)

    def list(self, username) -> List[Folder]:
        return [f for (u, _), f in self.rows.items() if u == username]

    def find(self, username, folderId):
        return self.rows.get((username, folderId))

    def add(self, username, folder):
        if folder.parentId is not None and (username, folder.parentId) not in self.rows:
            raise NotFoundError("parent")
        if (username, folder.id) in self.rows:
            raise ConflictError("duplicate")
        self.rows[(username, folder.id)] = folder

    def update(self, username, folderId, name, description):
        old = self.rows[(username, folderId)]
        self.rows[(username, folderId)] = Folder(old.id, old.parentId, name, description)

    def nameTaken(self, username, parentId, name, exceptId):
        return any(u == username and f.parentId == parentId and f.name.lower() == name.lower() and f.id != exceptId
                   for (u, _), f in self.rows.items())


class FakeFileIndex:
    def __init__(self, folders: FakeFolders):
        self.folders = folders
        self.rows: Dict[Tuple[str, str], FileEntry] = {}
        self.failUpsertWith: Optional[Exception] = None

    def list(self, username):
        return [e for (u, _), e in self.rows.items() if u == username]

    def find(self, username, entryId):
        return self.rows.get((username, entryId))

    def upsert(self, username, entry):
        if self.failUpsertWith:
            raise self.failUpsertWith
        old = self.rows.get((username, entry.id))
        if old is None:
            if entry.parentId is not None and not self.folders.find(username, entry.parentId):
                raise NotFoundError("parent")
            self.rows[(username, entry.id)] = entry
        else:
            self.rows[(username, entry.id)] = FileEntry(old.id, old.parentId, old.name, old.description,
                                                        entry.contentType, entry.size, old.favorite,
                                                        entry.dateModified, entry.mediaId)

    def update(self, username, entryId, name, description, favorite, dateModified):
        old = self.rows[(username, entryId)]
        self.rows[(username, entryId)] = FileEntry(
            old.id, old.parentId, name, description, old.contentType, old.size,
            old.favorite if favorite is None else favorite,
            old.dateModified if dateModified is None else dateModified, old.mediaId)

    def nameTaken(self, username, parentId, name, exceptId):
        return any(u == username and e.parentId == parentId and e.name.lower() == name.lower() and e.id != exceptId
                   for (u, _), e in self.rows.items())


class FakeContent:
    def __init__(self):
        self.blobs: Dict[str, bytes] = {}
        self._ids = itertools.count(1)

    def put(self, username, entryId, content, contentType):
        mediaId = f"m{next(self._ids)}"
        self.blobs[mediaId] = content
        return mediaId

    def get(self, mediaId):
        if mediaId not in self.blobs:
            raise NotFoundError("content")
        return self.blobs[mediaId]

    def delete(self, mediaId):
        self.blobs.pop(mediaId, None)


class FakeProvider:
    def __init__(self, profile: Optional[ProviderProfile] = None, configured: bool = True):
        self.profile = profile
        self._configured = configured
        self.lastCodeVerifier = None

    @property
    def configured(self):
        return self._configured

    def authorizationUrl(self, redirectUri, state, codeChallenge):
        return f"https://google.test/auth?state={state}&challenge={codeChallenge}&redirect={redirectUri}"

    def fetchProfile(self, code, redirectUri, codeVerifier):
        self.lastCodeVerifier = codeVerifier
        return self.profile


class Clock:
    def __init__(self, now: float = 1000.0):
        self.now = now

    def __call__(self) -> float:
        return self.now
