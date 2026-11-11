'''
UserManager.py

Use cases for user accounts: register, authenticate, edit, remove, and sign in with Google.
Depends only on the domain and on the ports in Ports.py.
'''
import secrets
from typing import Optional

from CommonErrors.Errors import ConflictError, UnauthorizedError, ValidationError
from UserLogin.application.Ports import PasswordHasher, UserRepository
from UserLogin.domain.Policies import (
    requireStrongPassword, requireValidEmail, requireValidUsername, usernameBase,
)
from UserLogin.domain.User import User

# RQ: The username cannot change after registration.
# RQ: The email must be unique.


class UserManager:
    def __init__(self, users: UserRepository, hasher: PasswordHasher):
        self.users = users
        self.hasher = hasher
        self._dummyHash = None

    # The checks that need no password: usernames and emails are well formed and not taken.
    def checkNewAccount(self, username: str, email: str):
        requireValidUsername(username)
        requireValidEmail(email)
        if self.users.findUsername(email) is not None:
            raise ConflictError("That username or email is already in use.")

    def registerUser(self, username: str, email: str, password: str) -> User:
        self.checkNewAccount(username, email)
        requireStrongPassword(password)
        if self.users.findUsername(username) is not None:
            raise ConflictError("Username already exists.")
        return self._create(username, email, password)

    # Creates an account if the username is free, without the password-strength rule (used to seed the admin).
    def seedUser(self, username: str, email: str, password: str):
        if self.users.get(username) is None:
            self._create(username, email, password)

    def _create(self, username: str, email: str, password: str) -> User:
        user = User(username, email)
        user.setPasswordHash(*self.hasher.hash(password))
        self.users.add(user)
        return user

    # Returns the User for a username or email and password, or None on any failure. The same result (and
    # about the same work) is returned for an unknown account and a wrong password, so callers cannot tell
    # which accounts exist.
    def authenticateUser(self, identifier: str, password: str) -> Optional[User]:
        username = self.users.findUsername(identifier.strip())
        user = self.users.get(username) if username else None
        if user is None or not user.hasPassword():
            self.hasher.verify(password, *self._dummy())
            return None
        salt, digest = user.getPasswordHash()
        return user if self.hasher.verify(password, salt, digest) else None

    def _dummy(self) -> tuple:
        if self._dummyHash is None:
            self._dummyHash = self.hasher.hash("not-a-real-password")
        return self._dummyHash

    def removeUser(self, user: User):
        self.users.delete(user.getUsername())

    def editUserPassword(self, user: User, currentPassword: str, newPassword: str):
        salt, digest = user.getPasswordHash()
        if not user.hasPassword() or not self.hasher.verify(currentPassword, salt, digest):
            raise UnauthorizedError("Current password is incorrect.")
        requireStrongPassword(newPassword)
        user.setPasswordHash(*self.hasher.hash(newPassword))
        self.users.updatePassword(user)

    def editUserEmail(self, user: User, newEmail: str):
        if not newEmail:
            raise ValidationError("Email is required.")
        self.users.update(user.getUsername(), email=newEmail)
        user.setEmail(newEmail)

    def setEncryptChoice(self, user: User, encryptChoice: bool):
        self.users.update(user.getUsername(), encryptChoice=encryptChoice)
        user.setEncryptChoice(encryptChoice)

    # Profile information for the user. The password is never exposed.
    def getUser(self, username: str) -> Optional[User]:
        return self.users.get(username)

    # Returns the username for a verified Google account, creating the account on first sign-in.
    def signInWithGoogle(self, googleID: str, email: str, name: str) -> str:
        username = self.users.findUsernameByGoogleID(googleID)
        if username is not None:
            return username
        # Not linked automatically: sign-up does not verify emails yet, so linking by email could hand this
        # Google user an account that someone else registered with their address and knows the password of.
        if self.users.findUsername(email) is not None:
            raise ConflictError("An account with this email already exists. Sign in with its password instead.")
        username = self._freeUsername(usernameBase(name, email))
        self.users.add(User(username, email), googleID=googleID)
        return username

    def _freeUsername(self, base: str) -> str:
        candidate = base
        while self.users.findUsername(candidate) is not None:
            candidate = f"{base}{secrets.randbelow(10000):04d}"
        return candidate
