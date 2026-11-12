'''
test_e2e_requirements.py

End-to-end test cases for the numbered requirements marked (DONE), against the RUNNING app over HTTP (real Postgres,
MongoDB and server in Docker). They are skipped when the app is not running.

  1. Upload a valid image and verify that the application accepts it.
  2. Upload an unsupported file type and verify error handling.
  5. Retrieve a previously uploaded document.
  9. Restart the application and verify document persistence.   (needs E2E_RESTART=1: it restarts the containers)
 10. Attempt unauthorized access to another user's document.
'''
import os
import subprocess
import time
import uuid
from pathlib import Path

import pytest

from Client import Client
from conftest import PASSWORD

REPO_ROOT = Path(__file__).resolve().parents[3]
PNG = b"\x89PNG\r\n\x1a\n" + bytes(range(64))
JPEG = b"\xff\xd8\xff\xe0\x00\x10JFIF" + bytes(range(64))
TEXT = b"Printed text that will be stored as a document.\n"
MAX_FILE_BYTES = 25 * 1024 * 1024
pytestmark = pytest.mark.e2e


def entry(client, entryId):
    return next((e for e in client.entries().json() if e["id"] == entryId), None)


# ---- 1. Upload a valid image and verify that the application accepts it ----------------------------------------

def test_req01_valid_png_is_accepted(alice):
    client, _ = alice
    response = client.upload("png1", "photo.png", PNG)
    assert response.status == 200
    assert response.json() == {"id": "png1", "size": len(PNG), "mimeType": "image/png"}
    saved = entry(client, "png1")
    assert saved["kind"] == "file" and saved["name"] == "photo.png" and saved["mimeType"] == "image/png"
    assert saved["parentId"] == "input" and saved["size"] == len(PNG)


def test_req01_valid_jpeg_is_accepted(alice):
    client, _ = alice
    response = client.upload("jpg1", "photo.jpg", JPEG)
    assert response.status == 200 and response.json()["mimeType"] == "image/jpeg"


def test_req01_the_type_comes_from_the_bytes_not_the_file_name(alice):
    client, _ = alice
    assert client.upload("png2", "really-a-png.txt", PNG).json()["mimeType"] == "image/png"


# ---- 2. Upload an unsupported file type and verify error handling ----------------------------------------------

UNSUPPORTED = {
    "windows program": b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00",
    "zip archive": b"PK\x03\x04\x14\x00\x00\x00\x08\x00",
    "mp4 video": b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00mp42isom",
    "random binary": bytes(range(256)),
}


@pytest.mark.parametrize("label", UNSUPPORTED)
def test_req02_unsupported_file_is_rejected_with_a_clear_error(alice, label):
    client, _ = alice
    entryId = "bad" + label.split()[0]
    response = client.upload(entryId, f"file-{entryId}.bin", UNSUPPORTED[label])
    assert response.status == 415
    assert response.detail == "Only PNG, JPG, PDF and text files are supported."
    assert entry(client, entryId) is None and client.download(entryId).status == 404  # nothing was stored


def test_req02_an_executable_cannot_pass_as_an_image_by_its_name(alice):
    client, _ = alice
    assert client.upload("badpng", "holiday.png", UNSUPPORTED["windows program"]).status == 415


def test_req02_a_file_over_the_size_limit_is_rejected(alice):
    client, _ = alice
    response = client.upload("huge", "huge.txt", b"a" * (MAX_FILE_BYTES + 1))
    assert response.status == 413 and "25MB" in response.detail
    assert entry(client, "huge") is None


def test_req02_a_bad_upload_does_not_disturb_existing_documents(alice):
    client, _ = alice
    assert client.upload("keep1", "keep.png", PNG).status == 200
    assert client.upload("keep2", "bad.bin", bytes(range(256))).status == 415
    assert client.download("keep1").body == PNG


def test_req02_other_invalid_requests_get_clear_errors(alice):
    client, _ = alice
    assert client.upload("bad id!", "x.txt", TEXT).status == 400                       # invalid id
    assert client.upload("okid", "a/b.txt", TEXT).status == 400                        # slash in the name
    assert client.upload("okid2", "x.txt", TEXT, parentId="does-not-exist").status == 404  # missing folder


# ---- 5. Retrieve a previously uploaded document ----------------------------------------------------------------

def test_req05_the_uploaded_document_comes_back_unchanged(alice):
    client, _ = alice
    assert client.upload("doc1", "retrieve-me.png", PNG).status == 200
    response = client.download("doc1")
    assert response.status == 200 and response.body == PNG
    headers = {key.lower(): value for key, value in response.headers.items()}
    assert headers["content-type"].startswith("image/png")
    assert "retrieve-me.png" in headers["content-disposition"] and headers["content-disposition"].startswith("attachment")
    assert headers["x-content-type-options"] == "nosniff"


def test_req05_a_text_document_comes_back_unchanged(alice):
    client, _ = alice
    assert client.upload("doc2", "notes.txt", TEXT).status == 200
    assert client.download("doc2").body == TEXT


def test_req05_the_document_is_still_listed_and_retrievable_later(alice):
    client, _ = alice
    assert client.upload("doc3", "later.png", PNG).status == 200
    assert client.upload("other", "other.txt", TEXT).status == 200  # unrelated activity in between
    assert "later.png" in client.names()
    assert client.download("doc3").body == PNG


def test_req05_after_replacing_a_document_the_newest_version_is_returned(alice):
    client, _ = alice
    assert client.upload("ver1", "versions.txt", b"first version").status == 200
    assert client.upload("ver1", "versions.txt", b"second version").status == 200
    assert client.download("ver1").body == b"second version"


def test_req05_an_unknown_document_is_not_found(alice):
    client, _ = alice
    response = client.download("never-uploaded")
    assert response.status == 404 and response.detail == "File not found."


# ---- 9. Restart the application and verify document persistence ------------------------------------------------

@pytest.mark.skipif(os.environ.get("E2E_RESTART") != "1",
                    reason="restarts the Docker containers; run with E2E_RESTART=1")
def test_req09_documents_persist_after_restarting_the_application(users):
    client, username = users.create("persist")
    assert client.upload("p-img", "persist.png", PNG).status == 200
    assert client.upload("p-txt", "persist.txt", TEXT).status == 200
    folder = client.request("POST", "/api/folders", {"id": "p-folder", "parentId": None, "name": "Kept", "description": "d"})
    assert folder.status == 200
    assert client.update("p-img", {"favorite": True}).status == 200
    before = sorted((e["id"], e["name"], e["kind"], bool(e.get("favorite"))) for e in client.entries().json())

    result = subprocess.run(["docker", "compose", "restart"], cwd=REPO_ROOT, capture_output=True, text=True, timeout=300)
    assert result.returncode == 0, result.stderr

    # Sessions live in the server's memory, so after a restart the user signs in again (like opening a fresh browser).
    fresh = Client()
    deadline = time.time() + 150
    while True:
        try:
            if fresh.login(username, PASSWORD).status == 200:
                break
        except OSError:
            pass  # the server is not accepting connections yet
        assert time.time() < deadline, "the app did not come back within 150 seconds"
        time.sleep(2)

    after = sorted((e["id"], e["name"], e["kind"], bool(e.get("favorite"))) for e in fresh.entries().json())
    assert after == before
    assert fresh.download("p-img").body == PNG
    assert fresh.download("p-txt").body == TEXT


# ---- 10. Attempt unauthorized access to another user's document ------------------------------------------------

@pytest.fixture(scope="module")
def secret(alice):
    client, _ = alice
    assert client.upload("secret1", "diary.txt", b"alice's private diary").status == 200
    folder = client.request("POST", "/api/folders", {"id": "alicedir", "parentId": None, "name": "Private", "description": ""})
    assert folder.status == 200
    return "secret1"


def test_req10_without_signing_in_nothing_is_accessible(secret):
    stranger = Client()
    assert stranger.entries().status == 401
    assert stranger.download(secret).status == 401
    assert stranger.upload("x1", "x.txt", TEXT).status == 401
    assert stranger.update(secret, {"name": "hacked.txt"}).status == 401


def test_req10_a_forged_session_is_refused(secret):
    forger = Client()
    forger.setSessionCookie("not-a-real-session-token")
    assert forger.entries().status == 401
    assert forger.download(secret).status == 401


def test_req10_another_user_cannot_read_the_document(secret, bob):
    client, _ = bob
    response = client.download(secret)
    assert response.status == 404 and b"private diary" not in response.body


def test_req10_another_user_cannot_see_it_in_their_listing(secret, bob):
    client, _ = bob
    assert entry(client, secret) is None and "diary.txt" not in client.names()


def test_req10_another_user_cannot_rename_or_favorite_it(secret, alice, bob):
    owner, _ = alice
    intruder, _ = bob
    assert intruder.update(secret, {"name": "hacked.txt"}).status == 404
    assert intruder.update(secret, {"favorite": True}).status == 404
    unchanged = entry(owner, secret)
    assert unchanged["name"] == "diary.txt" and not unchanged["favorite"]


def test_req10_another_user_cannot_overwrite_it_by_reusing_its_id(secret, alice, bob):
    owner, _ = alice
    intruder, _ = bob
    assert intruder.upload(secret, "mine.txt", b"bob's own file").status == 200  # becomes Bob's separate document
    assert owner.download(secret).body == b"alice's private diary"
    assert intruder.download(secret).body == b"bob's own file"


def test_req10_another_user_cannot_put_files_into_her_folder(secret, bob):
    client, _ = bob
    assert client.upload("intruder1", "x.txt", TEXT, parentId="alicedir").status == 404
    folder = client.request("POST", "/api/folders", {"id": "intruderdir", "parentId": "alicedir", "name": "x", "description": ""})
    assert folder.status == 404


def test_req10_signing_out_ends_access(users):
    client, _ = users.create("signout")
    client.upload("so1", "so.txt", TEXT)
    assert client.download("so1").status == 200
    assert client.request("POST", "/api/logout").status == 200
    assert client.download("so1").status == 401
