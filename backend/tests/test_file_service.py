import pytest

from CommonErrors.Errors import (
    ConflictError, NotFoundError, PayloadTooLargeError, UnsupportedMediaError, ValidationError,
)
from Fakes import FakeContent, FakeFileIndex, FakeFolders
from WI29_Server.application.FileService import FileService
from WI29_Server.domain.Files import MAX_FILE_BYTES, FileEntry, Folder

PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 8
ALICE, BOB = "alice", "bob"


@pytest.fixture
def parts():
    folders = FakeFolders()
    return folders, FakeFileIndex(folders), FakeContent()


@pytest.fixture
def service(parts):
    folders, files, content = parts
    times = iter(f"2026-01-01T00:00:{n:02d}" for n in range(60))
    svc = FileService(folders, files, content, now=lambda: next(times))
    svc.ensureDefaultFolders(ALICE)
    svc.ensureDefaultFolders(BOB)
    return svc


def names(service, user=ALICE):
    return sorted(e.name for e in service.listEntries(user))


def test_every_user_gets_input_and_output_folders_once(service):
    service.ensureDefaultFolders(ALICE)
    assert names(service) == ["Input", "Output"]


def test_listing_gives_a_new_user_their_default_folders(parts):
    folders, files, content = parts
    svc = FileService(folders, files, content)
    assert sorted(e.name for e in svc.listEntries("carol")) == ["Input", "Output"]


def test_create_folder_rules(service):
    service.createFolder(ALICE, "f1", None, "Trips", "")
    assert names(service) == ["Input", "Output", "Trips"]
    with pytest.raises(ConflictError):
        service.createFolder(ALICE, "f2", None, "trips", "")          # same name ignoring case
    with pytest.raises(NotFoundError, match="Parent folder"):
        service.createFolder(ALICE, "f3", "nope", "X", "")
    with pytest.raises(ValidationError, match="Invalid id"):
        service.createFolder(ALICE, "bad id!", None, "Y", "")
    with pytest.raises(ValidationError, match="slashes"):
        service.createFolder(ALICE, "f4", None, "a/b", "")
    service.createFolder(BOB, "f1", None, "Trips", "")                # another user may reuse the id and name


def test_input_and_output_names_are_fixed_but_description_can_change(service):
    service.updateEntry(ALICE, "input", "Hacked", "my note")
    folder = next(e for e in service.listEntries(ALICE) if e.id == "input")
    assert folder.name == "Input" and folder.description == "my note"


def test_put_file_detects_the_type_from_the_bytes(service, parts):
    size, contentType = service.putFile(ALICE, "img1", "input", "pic.png", "hi", PNG)
    assert (size, contentType) == (len(PNG), "image/png")
    assert service.getContent(ALICE, "img1") == (PNG, "image/png", "pic.png")
    service.putFile(ALICE, "t1", "input", "a.txt", "", b"hello")
    assert service.getContent(ALICE, "t1")[1] == "text/plain"


def test_put_file_rejects_bad_content(service):
    with pytest.raises(UnsupportedMediaError):
        service.putFile(ALICE, "b1", "input", "bad.bin", "", b"MZ\x00\x01binary")
    with pytest.raises(UnsupportedMediaError):
        service.putFile(ALICE, "b2", "input", "bad.bin", "", b"\xff\xfe\xfa")
    with pytest.raises(PayloadTooLargeError):
        service.putFile(ALICE, "b3", "input", "big.txt", "", b"a" * (MAX_FILE_BYTES + 1))


def test_put_file_checks_parent_and_name(service, parts):
    _, _, content = parts
    with pytest.raises(NotFoundError, match="Parent folder"):
        service.putFile(ALICE, "x1", "nope", "x.txt", "", b"x")
    assert content.blobs == {}                                         # the content stored first was removed
    service.putFile(ALICE, "x2", "input", "x.txt", "", b"x")
    with pytest.raises(ConflictError):
        service.putFile(ALICE, "x3", "input", "X.TXT", "", b"y")      # same name in the same folder
    assert len(content.blobs) == 1


def test_files_and_folders_share_one_namespace(service):
    service.createFolder(ALICE, "f1", "input", "notes", "")
    with pytest.raises(ConflictError):
        service.putFile(ALICE, "x1", "input", "Notes", "", b"x")


def test_replacing_content_keeps_the_name_and_removes_the_old_content(service, parts):
    _, _, content = parts
    service.putFile(ALICE, "t1", "input", "a.txt", "", b"first")
    service.putFile(ALICE, "t1", "input", "ignored.txt", "", b"second version")
    assert service.getContent(ALICE, "t1") == (b"second version", "text/plain", "a.txt")
    assert len(content.blobs) == 1


def test_failed_index_write_removes_the_new_content_and_keeps_the_old(service, parts):
    _, files, content = parts
    service.putFile(ALICE, "t1", "input", "a.txt", "", b"first")
    files.failUpsertWith = RuntimeError("database down")
    with pytest.raises(RuntimeError):
        service.putFile(ALICE, "t1", "input", "a.txt", "", b"second")
    files.failUpsertWith = None
    assert service.getContent(ALICE, "t1")[0] == b"first"
    assert len(content.blobs) == 1


def test_rename_updates_date_modified_but_favorite_does_not(service, parts):
    _, files, _ = parts
    service.putFile(ALICE, "t1", "input", "a.txt", "", b"x")
    created = files.find(ALICE, "t1").dateModified
    service.updateEntry(ALICE, "t1", None, None, favorite=True)
    assert files.find(ALICE, "t1").favorite and files.find(ALICE, "t1").dateModified == created
    service.updateEntry(ALICE, "t1", "b.txt", None)
    assert files.find(ALICE, "t1").name == "b.txt" and files.find(ALICE, "t1").dateModified != created
    service.updateEntry(ALICE, "t1", None, None, favorite=False)
    assert not files.find(ALICE, "t1").favorite


def test_only_files_can_be_favorites(service):
    with pytest.raises(ValidationError, match="Only files"):
        service.updateEntry(ALICE, "input", None, None, favorite=True)


def test_rename_cannot_collide(service):
    service.putFile(ALICE, "t1", "input", "a.txt", "", b"x")
    service.putFile(ALICE, "t2", "input", "b.txt", "", b"y")
    with pytest.raises(ConflictError):
        service.updateEntry(ALICE, "t2", "A.txt", None)
    service.updateEntry(ALICE, "t2", "B.TXT", None)                   # only the case changes: allowed


def test_users_cannot_see_or_change_each_others_items(service):
    service.putFile(ALICE, "secret", "input", "s.txt", "", b"alice's")
    assert [e.name for e in service.listEntries(BOB) if isinstance(e, FileEntry)] == []
    with pytest.raises(NotFoundError):
        service.getContent(BOB, "secret")
    with pytest.raises(NotFoundError):
        service.updateEntry(BOB, "secret", "hacked.txt", None)
    service.createFolder(ALICE, "af", None, "AliceDir", "")
    with pytest.raises(NotFoundError):                                  # cannot file anything under her folder
        service.putFile(BOB, "bf", "af", "x.txt", "", b"x")


def test_get_content_of_unknown_or_missing_content(service, parts):
    _, files, content = parts
    with pytest.raises(NotFoundError, match="File not found"):
        service.getContent(ALICE, "nope")
    service.putFile(ALICE, "t1", "input", "a.txt", "", b"x")
    content.blobs.clear()
    with pytest.raises(NotFoundError, match="File content not found"):
        service.getContent(ALICE, "t1")


def test_update_unknown_item(service):
    with pytest.raises(NotFoundError, match="Item not found"):
        service.updateEntry(ALICE, "nope", "x", None)
