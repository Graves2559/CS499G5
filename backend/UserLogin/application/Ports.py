'''
Ports.py

The interfaces the user use cases depend on. Infrastructure (databases, hashing algorithms) implements them;
the application layer never imports an implementation.
'''
from typing import Optional, Protocol

from UserLogin.domain.User import User


class UserRepository(Protocol):
    # A User with its password hash and security questions loaded, or None.
    def get(self, username: str) -> Optional[User]: ...

    # Usernames and emails are unique ignoring case. `identifier` is a username or an email address
    # (it is an email when it contains "@"). Returns the stored username, or None.
    def findUsername(self, identifier: str) -> Optional[str]: ...

    def findUsernameByGoogleID(self, googleID: str) -> Optional[str]: ...

    # Raises CommonErrors.Errors.ConflictError when the username or email is already in use.
    def add(self, user: User, googleID: Optional[str] = None) -> None: ...

    # The username itself is never updated. Raises ConflictError when the email is already in use.
    def update(self, username: str, email: Optional[str] = None, encryptChoice: Optional[bool] = None) -> None: ...

    def updatePassword(self, user: User) -> None: ...

    def delete(self, username: str) -> None: ...


class PasswordHasher(Protocol):
    def hash(self, password: str) -> tuple:
        '''Returns (salt, digest) for the password, with a new random salt.'''

    def verify(self, password: str, salt: bytes, digest: bytes) -> bool: ...
