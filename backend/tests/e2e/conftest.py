'''
conftest.py (end-to-end tests)

Fixtures for the tests that talk to the running app. If the app is not running, these tests are skipped.
Every user the tests create is removed afterwards (their rows in Postgres and their files in MongoDB).
'''
import subprocess
import uuid

import pytest

from Client import BASE_URL, Client

POSTGRES = "UserCredentials"
MONGO = "IMG_VID_TXT"
PASSWORD = "Str0ng#Pass1"


def _docker(*args):
    return subprocess.run(["docker", *args], capture_output=True, text=True, timeout=60)


class Users:
    '''Creates throw-away accounts and deletes them (with their data) at the end of the session.'''

    def __init__(self):
        self.created = []

    def create(self, label: str):
        username = f"e2e{label}{uuid.uuid4().hex[:8]}"
        client = Client()
        response = client.register(username, f"{username}@example.com", PASSWORD)
        assert response.status == 200, f"could not create the test user: {response.status} {response.body[:100]}"
        self.created.append(username)
        return client, username

    def cleanup(self):
        if not self.created:
            return
        names = ",".join(f"'{name}'" for name in self.created)  # names are generated above: letters and digits only
        psql = ["exec", POSTGRES, "psql", "-U", "postgres", "-At", "-d"]
        media = _docker(*psql, "indexDB", "-c", f"select media_id from index_entries where username in ({names})")
        ids = [line for line in media.stdout.split() if line]
        _docker(*psql, "indexDB", "-c", f"delete from index_entries where username in ({names}); "
                                        f"delete from storage_folders where username in ({names})")
        _docker(*psql, "user_db", "-c", f"delete from users where username in ({names})")
        if ids:
            script = (f"const ids={ids!r}.map(i=>ObjectId(i)); db.fs.chunks.deleteMany({{files_id:{{$in:ids}}}}); "
                      "db.fs.files.deleteMany({_id:{$in:ids}})")
            _docker("exec", MONGO, "mongosh", "--quiet", "UserFiles", "--eval", script)


@pytest.fixture(scope="session", autouse=True)
def app_is_running():
    try:
        Client().request("GET", "/api/me")
    except OSError:
        pytest.skip(f"the app is not running at {BASE_URL} (start it with `docker compose up -d`)")


@pytest.fixture(scope="session")
def users():
    registry = Users()
    yield registry
    registry.cleanup()


@pytest.fixture(scope="module")
def alice(users):
    return users.create("alice")


@pytest.fixture(scope="module")
def bob(users):
    return users.create("bob")
