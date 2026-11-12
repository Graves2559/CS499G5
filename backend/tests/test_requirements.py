'''
test_requirements.py

Test cases for the numbered requirements marked (DONE). They run the use cases against in-memory fakes, so they need
no server or database. The same requirements are tested against the running app in tests/e2e/.

  1. Upload a valid image and verify that the application accepts it.
  2. Upload an unsupported file type and verify error handling.
  5. Retrieve a previously uploaded document.
  9. Restart the application and verify document persistence.
 10. Attempt unauthorized access to another user's document.
'''
import pytest

from CommonErrors.Errors import (
    ConflictError, NotFoundError, PayloadTooLargeError, UnauthorizedError, UnsupportedMediaError,
)
from Fakes import FakeContent, FakeFileIndex, FakeFolders, FakeHasher, FakeUsers
from UserLogin.application.UserManager import UserManager
from WI29_Server.application.AuthService import AuthService
from WI29_Server.application.FileService import FileService
from WI29_Server.domain.Files import MAX_FILE_BYTES
from WI29_Server.infrastructure.MemoryStores import InMemorySessionStore, SlidingWindowLimiter

PNG = b"\x89PNG\r\n\x1a\n" + bytes(range(32))
JPEG = b"\xff\xd8\xff\xe0\x00\x10JFIF" + bytes(range(32))
PDF = b"%PDF-1.7\n1 0 obj\n<<>>\nendobj\n"
ALICE, BOB = "alice", "bob"


class App:
    '''One "running application": the stores hold the data, the services are rebuilt by restart().'''

    def __init__(self):
        self.folders = FakeFolders()
        self.files = FakeFileIndex(self.folders)
        self.content = FakeContent()
        self.users = FakeUsers()
        self.restart()

    def restart(self):
        self.service = FileService(self.folders, self.files, self.content)
        self.auth = AuthService(UserManager(self.users, FakeHasher()), InMemorySessionStore(3600),
                                SlidingWindowLimiter(5, 60), SlidingWindowLimiter(50, 60))


@pytest.fixture
def app():
    return App()


def upload(app, user, entryId, name, content, parent="input"):
    app.service.ensureDefaultFolders(user)
    return app.service.putFile(user, entryId, parent, name, "", content)


# ---- 1. Upload a valid image and verify that the application accepts it ----------------------------------------

@pytest.mark.parametrize("content,expectedType", [(PNG, "image/png"), (JPEG, "image/jpeg")])
def test_req01_valid_image_is_accepted(app, content, expectedType):
    size, contentType = upload(app, ALICE, "img1", "photo", content)
    assert (size, contentType) == (len(content), expectedType)
    stored = [e for e in app.service.listEntries(ALICE) if e.id == "img1"][0]
    assert stored.name == "photo" and stored.parentId == "input" and stored.contentType == expectedType
    assert app.content.blobs[stored.mediaId] == content


def test_req01_a_pdf_document_is_accepted_too(app):
    assert upload(app, ALICE, "doc1", "paper.pdf", PDF)[1] == "application/pdf"


def test_req01_the_type_comes_from_the_bytes_not_the_file_name(app):
    assert upload(app, ALICE, "img2", "actually-a-png.txt", PNG)[1] == "image/png"


# ---- 2. Upload an unsupported file type and verify error handling ---------------------------------------------

UNSUPPORTED = [
    ("windows program", b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00"),
    ("zip archive", b"PK\x03\x04\x14\x00\x00\x00\x08\x00"),
    ("mp4 video", b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00mp42isom"),
    ("random binary", bytes(range(256))),
    ("invalid text encoding", b"\xff\xfe\xfa\xfb"),
]


@pytest.mark.parametrize("label,content", UNSUPPORTED, ids=[label for label, _ in UNSUPPORTED])
def test_req02_unsupported_file_is_rejected_and_nothing_is_stored(app, label, content):
    with pytest.raises(UnsupportedMediaError, match="Only PNG, JPG, PDF and text"):
        upload(app, ALICE, "bad1", "x.bin", content)
    assert app.content.blobs == {}
    assert [e.name for e in app.service.listEntries(ALICE) if e.id == "bad1"] == []


def test_req02_a_dangerous_file_cannot_pass_as_an_image_by_its_name(app):
    with pytest.raises(UnsupportedMediaError):
        upload(app, ALICE, "bad2", "holiday.png", UNSUPPORTED[0][1])


def test_req02_a_file_over_the_size_limit_is_rejected(app):
    with pytest.raises(PayloadTooLargeError, match="25MB"):
        upload(app, ALICE, "big", "big.txt", b"a" * (MAX_FILE_BYTES + 1))
    assert app.content.blobs == {}


def test_req02_a_failed_upload_leaves_earlier_documents_untouched(app):
    upload(app, ALICE, "ok1", "ok.png", PNG)
    with pytest.raises(UnsupportedMediaError):
        upload(app, ALICE, "bad3", "bad.bin", bytes(range(256)))
    assert app.service.getContent(ALICE, "ok1")[0] == PNG


# ---- 5. Retrieve a previously uploaded document ---------------------------------------------------------------

def test_req05_the_uploaded_document_comes_back_unchanged(app):
    upload(app, ALICE, "img1", "photo.png", PNG)
    data, contentType, name = app.service.getContent(ALICE, "img1")
    assert (data, contentType, name) == (PNG, "image/png", "photo.png")


def test_req05_retrieving_after_replacing_returns_the_newest_version(app):
    upload(app, ALICE, "t1", "notes.txt", b"first version")
    upload(app, ALICE, "t1", "notes.txt", b"second version")
    assert app.service.getContent(ALICE, "t1")[0] == b"second version"
    assert len(app.content.blobs) == 1  # the old version was removed, not leaked


def test_req05_an_unknown_document_is_not_found(app):
    with pytest.raises(NotFoundError, match="File not found"):
        app.service.getContent(ALICE, "never-uploaded")


# ---- 9. Restart the application and verify document persistence -----------------------------------------------

def test_req09_documents_survive_a_restart(app):
    upload(app, ALICE, "img1", "photo.png", PNG)
    upload(app, ALICE, "t1", "notes.txt", b"my notes")
    before = sorted(e.name for e in app.service.listEntries(ALICE))
    app.restart()  # new services, same databases
    assert sorted(e.name for e in app.service.listEntries(ALICE)) == before
    assert app.service.getContent(ALICE, "img1")[0] == PNG
    assert app.service.getContent(ALICE, "t1")[0] == b"my notes"


def test_req09_the_account_survives_a_restart_and_signs_in_again(app):
    app.auth.register("alice", "alice@example.com", "Str0ng#Pass")
    oldToken = app.auth.login("alice", "Str0ng#Pass")
    app.restart()
    assert app.auth.username(oldToken) is None  # sessions live in memory: signing in again is needed
    assert app.auth.username(app.auth.login("alice", "Str0ng#Pass")) == "alice"


# ---- 10. Attempt unauthorized access to another user's document ------------------------------------------------

def test_req10_another_user_cannot_read_a_document(app):
    upload(app, ALICE, "secret", "diary.txt", b"alice's secret")
    app.service.ensureDefaultFolders(BOB)
    with pytest.raises(NotFoundError):
        app.service.getContent(BOB, "secret")


def test_req10_another_user_cannot_see_it_in_listings(app):
    upload(app, ALICE, "secret", "diary.txt", b"alice's secret")
    assert [e.name for e in app.service.listEntries(BOB)] == ["Input", "Output"]


def test_req10_another_user_cannot_rename_or_favorite_it(app):
    upload(app, ALICE, "secret", "diary.txt", b"alice's secret")
    app.service.ensureDefaultFolders(BOB)
    with pytest.raises(NotFoundError):
        app.service.updateEntry(BOB, "secret", "hacked.txt", None)
    with pytest.raises(NotFoundError):
        app.service.updateEntry(BOB, "secret", None, None, favorite=True)
    assert app.service.getContent(ALICE, "secret")[2] == "diary.txt"


def test_req10_another_user_cannot_overwrite_it_by_reusing_its_id(app):
    upload(app, ALICE, "secret", "diary.txt", b"alice's secret")
    upload(app, BOB, "secret", "mine.txt", b"bob's own file")  # same id, different owner: a separate document
    assert app.service.getContent(ALICE, "secret")[0] == b"alice's secret"
    assert app.service.getContent(BOB, "secret")[0] == b"bob's own file"


def test_req10_another_user_cannot_file_things_into_her_folder(app):
    app.service.ensureDefaultFolders(ALICE)
    app.service.createFolder(ALICE, "af", None, "Private", "")
    app.service.ensureDefaultFolders(BOB)
    with pytest.raises(NotFoundError):
        app.service.putFile(BOB, "x1", "af", "x.txt", "", b"x")
    with pytest.raises(NotFoundError):
        app.service.createFolder(BOB, "x2", "af", "sub", "")


def test_req10_no_session_means_no_access(app):
    assert app.auth.username(None) is None
    assert app.auth.username("a-made-up-token") is None


def test_req10_wrong_credentials_give_no_session(app):
    app.auth.register("alice", "alice@example.com", "Str0ng#Pass")
    with pytest.raises(UnauthorizedError):
        app.auth.login("alice", "wrong")
