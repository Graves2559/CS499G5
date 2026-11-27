'''
test_key_service.py

KeyService composes UserLogin's UserManager (security questions) with Security's EncryptionManager (the
passphrase/recovery-code reset cases), gated by RQ4's confirmation code. Real UserManager/EncryptionManager
are used (only their DB-backed repositories are faked), the same pattern as the rest of this suite.
'''
import pytest

from CommonErrors.Errors import CorruptedDataError, UnauthorizedError, ValidationError
from Fakes import FakeHasher, FakeKeyRecords, FakeUsers
from Security.application.EncryptionManager import EncryptionManager
from Security.infrastructure.AesGcmCypher import AesGcmCypher
from Security.infrastructure.InMemoryResetConfirmations import InMemoryResetConfirmations
from UserLogin.application.UserManager import UserManager
from WI29_Server.application.KeyService import KeyService

STRONG = "Str0ng#Pass"
PASSPHRASE = "correct horse battery staple"
NEW_PASSPHRASE = "a different passphrase"


@pytest.fixture
def accounts():
    return UserManager(FakeUsers(), FakeHasher())


@pytest.fixture
def vault():
    return EncryptionManager(FakeKeyRecords(), AesGcmCypher(), InMemoryResetConfirmations())


@pytest.fixture
def keyService(accounts, vault):
    return KeyService(accounts, vault)


@pytest.fixture
def alice(accounts):
    return accounts.registerUser("alice", "alice@example.com", STRONG)


def confirm(keyService, username="alice"):
    return keyService.requestResetConfirmation(username)


def test_case1_change_passphrase_without_security_questions_configured(keyService, vault, alice):
    keyVersion, ciphertext = vault.encryptContent("alice", PASSPHRASE, b"diary entry")
    code = confirm(keyService)
    keyService.changePassphrase(alice, code, PASSPHRASE, NEW_PASSPHRASE)
    assert vault.decryptContent("alice", NEW_PASSPHRASE, keyVersion, ciphertext) == b"diary entry"


def test_case1_requires_correct_security_answers_when_configured(keyService, accounts, alice):
    keyService.setupSecurityQuestions(alice, {"First pet?": "Rex"})
    code = confirm(keyService)
    with pytest.raises(UnauthorizedError, match="incorrect"):
        keyService.changePassphrase(alice, code, PASSPHRASE, NEW_PASSPHRASE, {"First pet?": "wrong"})


def test_case1_succeeds_with_correct_security_answers(keyService, vault, alice):
    keyService.setupSecurityQuestions(alice, {"First pet?": "Rex"})
    vault.encryptContent("alice", PASSPHRASE, b"diary entry")
    code = confirm(keyService)
    keyService.changePassphrase(alice, code, PASSPHRASE, NEW_PASSPHRASE, {"First pet?": " rex "})


def test_reset_without_rq4_confirmation_is_rejected(keyService, vault, alice):
    vault.encryptContent("alice", PASSPHRASE, b"diary entry")
    with pytest.raises(ValidationError, match="confirmation code"):
        keyService.changePassphrase(alice, "000000", PASSPHRASE, NEW_PASSPHRASE)


def test_case2_recover_with_recovery_code(keyService, vault, alice):
    keyVersion, ciphertext = vault.encryptContent("alice", PASSPHRASE, b"diary entry")
    recoveryCode = keyService.generateRecoveryCode(alice, PASSPHRASE)
    code = confirm(keyService)
    keyService.recoverWithRecoveryCode(alice, code, recoveryCode, NEW_PASSPHRASE)
    assert vault.decryptContent("alice", NEW_PASSPHRASE, keyVersion, ciphertext) == b"diary entry"


def test_generate_recovery_code_does_not_need_rq4_confirmation(keyService, vault, alice):
    vault.encryptContent("alice", PASSPHRASE, b"diary entry")
    vault_code = keyService.generateRecoveryCode(alice, PASSPHRASE)
    assert vault_code


def test_case3_wipe_and_reprovision_returns_a_fresh_recovery_code(keyService, vault, alice):
    oldVersion, ciphertext = vault.encryptContent("alice", PASSPHRASE, b"diary entry")
    code = confirm(keyService)
    recoveryCode = keyService.wipeAndReprovision(alice, code, NEW_PASSPHRASE)
    assert recoveryCode
    with pytest.raises(CorruptedDataError):
        vault.decryptContent("alice", NEW_PASSPHRASE, oldVersion, ciphertext)
    newVersion, newCiphertext = vault.encryptContent("alice", NEW_PASSPHRASE, b"fresh start")
    assert vault.decryptContent("alice", NEW_PASSPHRASE, newVersion, newCiphertext) == b"fresh start"
