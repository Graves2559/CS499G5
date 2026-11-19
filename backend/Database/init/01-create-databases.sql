-- 01-create-databases.sql
-- Creates one database per DatabaseAdapter subclass in backend/Security/Database.py.
-- Each adapter connects with its own connectionString, so these are kept as
-- separate databases (not just schemas) within the same Postgres instance --
-- consistent with the adapters never needing to JOIN across each other.

CREATE DATABASE user_db;
CREATE DATABASE keyrecord_db;
CREATE DATABASE "indexDB";   -- quoted to keep the capital letters: small index of entries (metadata + media_id)
