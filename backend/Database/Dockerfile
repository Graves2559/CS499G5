# Dockerfile
# Builds a Postgres image pre-loaded with the schema for the 3 databases that
# back backend/Security/Database.py's 3 DatabaseAdapter subclasses:
#   - user_db      -> UserDatabaseAdapter
#   - keyrecord_db -> KeyRecordDatabaseAdapter
#   - indexDB      -> JournalEntryDatabaseAdapter
#
# Build:
#   docker build -t journaling-postgres backend/Database
# Run (standalone, without docker-compose):
#   docker run -d --name journaling-postgres -p 5432:5432 \
#     -e POSTGRES_PASSWORD=changeme journaling-postgres
# Prefer `docker compose up` (see docker-compose.yml) for local development --
# it also persists data in a named volume across restarts.

FROM postgres:16-alpine

# The official postgres image runs every *.sql/*.sh file in this directory,
# in alphabetical order, exactly once -- the first time the data directory is
# initialized (i.e. NOT on every container restart, only on a fresh volume).
COPY init/ /docker-entrypoint-initdb.d/
