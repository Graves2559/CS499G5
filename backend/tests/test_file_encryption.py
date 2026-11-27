'''
test_file_encryption.py

FileService's integration with a SymmetricKeyVault (Security's EncryptionManager, wired with the real
AesGcmCypher so this exercises actual encryption, not a stand-in): uploading with a passphrase encrypts the
content at rest, downloading needs the same passphrase, and rotating the key re-encrypts existing files
under a fresh dataKey without changing the passphrase.
'''
import pytest

from CommonErrors.Errors import CorruptedDataError, ValidationError
from Fakes import FakeContent, FakeFileIndex, FakeFolders, FakeKeyRecords
from Security.application.EncryptionManager import EncryptionManager
from Security.infrastructure.AesGcmCypher import AesGcmCypher
from Security.infrastructure.InMemoryResetConfirmations import InMemoryResetConfirmations
from WI29_Server.application.FileService import FileService

ALICE = "alice"
PASSPHRASE = "correct horse battery staple"


@pytest.fixture
def vault():
    return EncryptionManager(FakeKeyRecords(), AesGcmCypher(), InMemoryResetConfirmations())


@pytest.fixture
def service(vault):
    folders = FakeFolders()
    files = FakeFileIndex(folders)
    content = FakeContent()
    svc = FileService(folders, files, content, vault=vault)
    svc.ensureDefaultFolders(ALICE)
    return svc


def test_uploading_with_a_passphrase_stores_ciphertext_not_plaintext(service):
    plaintext = b"%PDF-1.7\nmy private diary entry"
    service.putFile(ALICE, "doc1", "input", "diary.pdf", "", plaintext, symmetricKey=PASSPHRASE)
    stored = [e for e in service.listEntries(ALICE) if e.id == "doc1"][0]
    assert stored.keyVersion == 1
    assert service.content.blobs[stored.mediaId] != plaintext


def test_downloading_with_the_right_passphrase_returns_the_original_content(service):
    plaintext = b"%PDF-1.7\nmy private diary entry"
    service.putFile(ALICE, "doc1", "input", "diary.pdf", "", plaintext, symmetricKey=PASSPHRASE)
    data, contentType, name = service.getContent(ALICE, "doc1", symmetricKey=PASSPHRASE)
    assert (data, contentType, name) == (plaintext, "application/pdf", "diary.pdf")


def test_downloading_without_a_passphrase_is_rejected(service):
    service.putFile(ALICE, "doc1", "input", "diary.pdf", "", b"%PDF-1.7\nsecret", symmetricKey=PASSPHRASE)
    with pytest.raises(ValidationError, match="Enter your passphrase"):
        service.getContent(ALICE, "doc1")


def test_downloading_with_the_wrong_passphrase_is_rejected(service):
    service.putFile(ALICE, "doc1", "input", "diary.pdf", "", b"%PDF-1.7\nsecret", symmetricKey=PASSPHRASE)
    with pytest.raises(CorruptedDataError):
        service.getContent(ALICE, "doc1", symmetricKey="wrong passphrase")


def test_uploading_without_a_passphrase_stores_content_unencrypted_as_before(service):
    plaintext = b"%PDF-1.7\nnot encrypted"
    service.putFile(ALICE, "doc2", "input", "notes.pdf", "", plaintext)
    stored = [e for e in service.listEntries(ALICE) if e.id == "doc2"][0]
    assert stored.keyVersion is None
    assert service.getContent(ALICE, "doc2")[0] == plaintext


def test_rotating_the_key_keeps_every_encrypted_file_readable_under_the_same_passphrase(service):
    service.putFile(ALICE, "doc1", "input", "a.pdf", "", b"%PDF-1.7\nfile a", symmetricKey=PASSPHRASE)
    service.putFile(ALICE, "doc2", "input", "b.pdf", "", b"%PDF-1.7\nfile b", symmetricKey=PASSPHRASE)
    service.putFile(ALICE, "doc3", "input", "c.pdf", "", b"%PDF-1.7\nnot encrypted")  # untouched by rotation

    service.rotateEncryptionKey(ALICE, PASSPHRASE)

    entries = {e.id: e for e in service.listEntries(ALICE) if e.id.startswith("doc")}
    assert entries["doc1"].keyVersion == 2 and entries["doc2"].keyVersion == 2
    assert entries["doc3"].keyVersion is None
    assert service.getContent(ALICE, "doc1", symmetricKey=PASSPHRASE)[0] == b"%PDF-1.7\nfile a"
    assert service.getContent(ALICE, "doc2", symmetricKey=PASSPHRASE)[0] == b"%PDF-1.7\nfile b"
    assert service.getContent(ALICE, "doc3")[0] == b"%PDF-1.7\nnot encrypted"


def test_encryption_unavailable_without_a_vault():
    folders = FakeFolders()
    svc = FileService(folders, FakeFileIndex(folders), FakeContent())  # no vault configured
    svc.ensureDefaultFolders(ALICE)
    with pytest.raises(ValidationError, match="Encryption is not available"):
        svc.putFile(ALICE, "doc1", "input", "a.pdf", "", b"%PDF-1.7\nfile", symmetricKey=PASSPHRASE)
