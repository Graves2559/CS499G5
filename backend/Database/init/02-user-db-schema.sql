-- 02-user-db-schema.sql
-- Schema for UserDatabaseAdapter (backend/Security/Database.py).
-- Mirrors User.py's persisted fields: username (the unique identifier -- there
-- is no separate user ID; usernames cannot be changed after registration),
-- email, and (hashed)
-- security-question answers set up via HelpDesk.setupSecurityQuestions.
--
-- IMPORTANT: the user's private key passphrase (User.privateKey) is NEVER
-- stored here, or anywhere -- that is the entire point of the zero-knowledge
-- design in KeyManager/Cypher. Only a login password hash belongs here, and
-- it must be hashed by the application (e.g. Argon2id) before being passed
-- to this table; this schema does not do any hashing itself.

\c user_db

CREATE TABLE users (
    username        TEXT PRIMARY KEY,               -- unique; the identifier every other table references
    email           TEXT NOT NULL UNIQUE,
    password_hash   TEXT,                           -- hashed login credential; NOT the private key passphrase
                                                      -- NULL for accounts that only sign in with Google
    google_id       TEXT UNIQUE,                    -- Google's stable account id ("sub"); NULL for password-only accounts
    encrypt_choice  BOOLEAN NOT NULL DEFAULT true,   -- whether this user's journal entries get encrypted
                                                      -- (see User.py/EncryptionManager.Encrypt -- encrypt()
                                                      -- refuses when false; decrypt() persists content back
                                                      -- to plaintext_data when false, read-only when true)
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Usernames and emails are unique ignoring case ("Bob" and "bob" are the same account).
CREATE UNIQUE INDEX uq_users_username_lower ON users (lower(username));
CREATE UNIQUE INDEX uq_users_email_lower ON users (lower(email));

-- One row per security question set up via HelpDesk.setupSecurityQuestions.
-- salt/answer_hash mirror User.setSecurityAnswerHash(question, salt, answerHash)
-- exactly -- plaintext answers are never computed or stored past the hashing step.
CREATE TABLE security_questions (
    username     TEXT NOT NULL REFERENCES users(username) ON DELETE CASCADE,
    question     TEXT NOT NULL,
    salt         BYTEA NOT NULL,
    answer_hash  BYTEA NOT NULL,
    PRIMARY KEY (username, question)
);
