'''
UserManager.py

Use cases for user accounts: register, authenticate, edit, and remove. There is no Google sign-in (Security
README RQ2): every account signs in with its own username/email and password.
Depends only on the domain and on the ports in Ports.py.
'''
from typing import Optional

from CommonErrors.Errors import ConflictError, UnauthorizedError, ValidationError
from UserLogin.application.Ports import PasswordHasher, UserRepository
from UserLogin.domain.Policies import requireStrongPassword, requireValidEmail, requireValidUsername
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

    # Starts binding `email` to the account. Returns the verification code, which the caller must send to that
    # address and never show to the requester.
    def requestEmailVerification(self, user: User, email: str) -> str:
        requireValidEmail(email)
        found = self.users.findUsername(email)
        if found is not None and found.lower() != user.getUsername().lower():
            raise ConflictError("That email is already in use.")
        return user.requestEmailVerification(email)

    # Binds the pending email only when the code is correct; otherwise raises ValidationError.
    def verifyEmail(self, user: User, code: str):
        previous = user.getEmail()
        email = user.verifyEmail(code)
        try:
            self.users.update(user.getUsername(), email=email)
        except ConflictError:
            user.setEmail(previous)
            raise

    def setEncryptChoice(self, user: User, encryptChoice: bool):
        self.users.update(user.getUsername(), encryptChoice=encryptChoice)
        user.setEncryptChoice(encryptChoice)

    # RQ5/RQ8/RQ9: sets up (or replaces) the user's security-question answers, gating the half-hold removal
    # and (Case 1 of) resetting the symmetric key. Answers are hashed (never stored in the clear); the same
    # question text answered the same way always verifies, regardless of case/whitespace.
    def setupSecurityQuestions(self, user: User, questionAnswers: dict):
        if not questionAnswers:
            raise ValidationError("At least one security question is required.")
        user.getSecurityQuestions().clear()
        for question, answer in questionAnswers.items():
            salt, answerHash = self.hasher.hash(_normalizeAnswer(answer))
            user.setSecurityAnswerHash(question, salt, answerHash)
        self.users.replaceSecurityQuestions(user.getUsername(), user.getSecurityQuestions())

    # True if every configured question is answered correctly (constant-time compare per question). If the
    # user never set up any security questions, this gate is simply not in effect (vacuously true).
    def verifySecurityAnswers(self, user: User, candidateAnswers: dict) -> bool:
        for question, record in user.getSecurityQuestions().items():
            candidate = candidateAnswers.get(question)
            if candidate is None or not self.hasher.verify(_normalizeAnswer(candidate), record["salt"], record["answerHash"]):
                return False
        return True

    # Profile information for the user. The password is never exposed.
    def getUser(self, username: str) -> Optional[User]:
        return self.users.get(username)


def _normalizeAnswer(answer: str) -> str:
    return answer.strip().lower()
