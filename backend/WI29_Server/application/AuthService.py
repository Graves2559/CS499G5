'''
AuthService.py

Use cases for signing in: password login, registration, and sessions.
The accounts themselves come through the Accounts port (UserLogin's UserManager implements it); this adds sessions,
abuse limits, and "what happens when someone signs in" on top.

# RQ2 (Security/README.md): there is no Google sign-in. Every account logs in with its own password.
'''
from typing import Callable, Optional

from CommonErrors.Errors import TooManyRequestsError, UnauthorizedError
from WI29_Server.application.Ports import Account, Accounts, AttemptLimiter, SessionStore


class AuthService:
    # onSignedIn(username) runs every time a session starts, e.g. to give a new user their default folders.
    def __init__(self, accounts: Accounts, sessions: SessionStore,
                 loginLimiter: AttemptLimiter, registerLimiter: AttemptLimiter,
                 onSignedIn: Optional[Callable[[str], None]] = None):
        self.accounts = accounts
        self.sessions = sessions
        self.loginLimiter = loginLimiter
        self.registerLimiter = registerLimiter
        self.onSignedIn = onSignedIn

    # Creates the account if it does not exist yet. The registration password rule is not applied to it.
    def seedAccount(self, username: str, email: str, password: str):
        self.accounts.seedUser(username, email, password)

    # Returns a session token. `identifier` is a username or an email address.
    def login(self, identifier: str, password: str) -> str:
        key = identifier.strip().lower()
        if self.loginLimiter.blocked(key):
            raise TooManyRequestsError("Too many failed attempts. Try again in a minute.")
        user = self.accounts.authenticateUser(identifier, password)
        if user is None:
            self.loginLimiter.record(key)
            raise UnauthorizedError("Incorrect username or password.")
        self.loginLimiter.reset(key)
        return self._startSession(user.getUsername())

    # Creates the account and signs it in.
    def register(self, username: str, email: str, password: str) -> str:
        username, email = username.strip(), email.strip()
        self.accounts.checkNewAccount(username, email)
        if self.registerLimiter.blocked("register"):
            raise TooManyRequestsError("Too many accounts created recently. Try again in a minute.")
        self.registerLimiter.record("register")
        user = self.accounts.registerUser(username, email, password)
        return self._startSession(user.getUsername())

    def username(self, token: Optional[str]) -> Optional[str]:
        return self.sessions.username(token)

    def logout(self, token: Optional[str]):
        self.sessions.delete(token)

    # Profile information for the signed-in user (e.g. the encryption preference). The password is never
    # exposed, and the symmetric-key passphrase is never stored here or anywhere server-side.
    def getUser(self, username: str) -> Optional[Account]:
        return self.accounts.getUser(username)

    def setEncryptChoice(self, user: Account, encryptChoice: bool):
        self.accounts.setEncryptChoice(user, encryptChoice)

    def _startSession(self, username: str) -> str:
        if self.onSignedIn:
            self.onSignedIn(username)
        return self.sessions.create(username)
