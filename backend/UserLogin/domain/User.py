'''
User.py

Domain entity: user information within the journaling program. Knows nothing about databases or hashing
algorithms -- it only holds the (already hashed) password, which the application layer sets and verifies.
'''

# RQ: The email is required for account recovery and communication, and must be unique.
# RQ: The username cannot change after registration (every other table references it).
# RQ: The plaintext password is never stored; only a salted hash is kept.


class User:
    def __init__(self, username: str, email: str):
        self.username = username
        self.email = email

        # Should not be stored inside the DB. Unlocks the encrypted data key.
        self.rawSymmetricKey = ""

        self._passwordSalt = b""
        self._passwordHash = b""

        # question -> {"salt": bytes, "answerHash": bytes}. Empty until the user opts in.
        self.securityQuestions: dict = {}
        self.encryptChoice = True

    def __repr__(self):
        return f"User(username={self.username!r}, email={self.email!r})"

    def getUsername(self) -> str:
        return self.username

    def getEmail(self) -> str:
        return self.email

    def setEmail(self, email: str):
        self.email = email

    def getEncryptChoice(self) -> bool:
        return self.encryptChoice

    def setEncryptChoice(self, encryptChoice: bool):
        self.encryptChoice = encryptChoice

    def setPrivateKey(self, phrase: str):
        self.rawSymmetricKey = phrase

    def getPrivateKey(self) -> str:
        return self.rawSymmetricKey

    def setPasswordHash(self, salt: bytes, passwordHash: bytes):
        self._passwordSalt = salt
        self._passwordHash = passwordHash

    def getPasswordHash(self) -> tuple:
        return self._passwordSalt, self._passwordHash

    def hasPassword(self) -> bool:
        return bool(self._passwordHash)

    def setSecurityAnswerHash(self, question: str, salt: bytes, answerHash: bytes):
        self.securityQuestions[question] = {"salt": salt, "answerHash": answerHash}

    def getSecurityQuestions(self) -> dict:
        return self.securityQuestions
