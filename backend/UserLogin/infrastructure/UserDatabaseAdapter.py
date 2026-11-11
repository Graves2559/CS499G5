'''
UserDatabaseAdapter.py

Implements the UserRepository port: stores User() information in the user_db Postgres database
(users and security_questions tables, see Database/init/02-user-db-schema.sql).
'''
import psycopg
from psycopg.errors import UniqueViolation

from CommonErrors.Errors import ConflictError
from UserLogin.domain.User import User

_HASH_PREFIX = "scrypt"


# password_hash is a TEXT column: "scrypt$<salt hex>$<hash hex>". Only the hash is stored, never the password.
def encodePasswordHash(salt: bytes, passwordHash: bytes) -> str:
    return f"{_HASH_PREFIX}${salt.hex()}${passwordHash.hex()}"


def decodePasswordHash(stored: str) -> tuple:
    prefix, saltHex, hashHex = stored.split("$")
    if prefix != _HASH_PREFIX:
        raise ValueError("Unsupported password hash format.")
    return bytes.fromhex(saltHex), bytes.fromhex(hashHex)


class UserDatabaseAdapter:
    def __init__(self, connectionString: str):
        self.connectionString = connectionString
        self._conn = None

    # autocommit: every statement takes effect immediately.
    def connect(self):
        if self._conn is None or self._conn.closed:
            self._conn = psycopg.connect(self.connectionString, autocommit=True)
        return self._conn

    def disconnect(self):
        if self._conn is not None and not self._conn.closed:
            self._conn.close()

    # googleID is set for accounts created through "Continue with Google" (they have no password).
    def add(self, user: User, googleID: str = None):
        conn = self.connect()
        salt, passwordHash = user.getPasswordHash()
        stored = encodePasswordHash(salt, passwordHash) if user.hasPassword() else None
        try:
            with conn.transaction():
                conn.execute(
                    "INSERT INTO users (username, email, password_hash, encrypt_choice, google_id) VALUES (%s, %s, %s, %s, %s)",
                    (user.getUsername(), user.getEmail(), stored, user.getEncryptChoice(), googleID),
                )
                for question, qa in user.getSecurityQuestions().items():
                    conn.execute(
                        "INSERT INTO security_questions (username, question, salt, answer_hash) VALUES (%s, %s, %s, %s)",
                        (user.getUsername(), question, qa["salt"], qa["answerHash"]),
                    )
        except UniqueViolation:
            # username is the PRIMARY KEY and email is UNIQUE -- either can collide.
            raise ConflictError("That username or email is already in use.")

    # Returns a User with its password hash and security questions loaded, or None if it doesn't exist.
    def get(self, username: str):
        conn = self.connect()
        row = conn.execute(
            "SELECT username, email, password_hash, encrypt_choice FROM users WHERE username = %s", (username,)
        ).fetchone()
        if row is None:
            return None
        dbUsername, email, stored, encryptChoice = row
        user = User(dbUsername, email)
        user.setEncryptChoice(encryptChoice)
        if stored:
            user.setPasswordHash(*decodePasswordHash(stored))
        for question, salt, answerHash in conn.execute(
            "SELECT question, salt, answer_hash FROM security_questions WHERE username = %s", (username,)
        ).fetchall():
            user.setSecurityAnswerHash(question, bytes(salt), bytes(answerHash))
        return user

    def findUsernameByGoogleID(self, googleID: str):
        row = self.connect().execute("SELECT username FROM users WHERE google_id = %s", (googleID,)).fetchone()
        return row[0] if row else None

    # Usernames and emails are unique ignoring case. Returns the stored username, or None.
    def findUsername(self, identifier: str):
        column = "email" if "@" in identifier else "username"
        row = self.connect().execute(
            f"SELECT username FROM users WHERE lower({column}) = lower(%s)", (identifier,)
        ).fetchone()
        return row[0] if row else None

    # The username itself is never updated -- it is the primary key every other table references.
    def update(self, username: str, email: str = None, encryptChoice: bool = None):
        conn = self.connect()
        try:
            if email is not None:
                conn.execute("UPDATE users SET email = %s WHERE username = %s", (email, username))
        except UniqueViolation:
            raise ConflictError("That email is already in use.")
        if encryptChoice is not None:
            conn.execute("UPDATE users SET encrypt_choice = %s WHERE username = %s", (encryptChoice, username))

    def updatePassword(self, user: User):
        salt, passwordHash = user.getPasswordHash()
        self.connect().execute(
            "UPDATE users SET password_hash = %s WHERE username = %s",
            (encodePasswordHash(salt, passwordHash), user.getUsername()),
        )

    def delete(self, username: str):
        self.connect().execute("DELETE FROM users WHERE username = %s", (username,))
