'''
test_security.py

Use cases for a user's encryption: encrypting/decrypting content, rotating the symmetric key, and resetting
it when the passphrase is lost (RQ4's email-confirmation gate + the 3 HelpDesk cases). Run against the real
AesGcmCypher (fast, deterministic, pure) and the real InMemoryResetConfirmations, with only KeyRecordRepository
faked (it needs a real database in production) -- the same pattern as the rest of this test suite.
'''
import pytest

from CommonErrors.Errors import CorruptedDataError, NotFoundError, ValidationError
from Fakes import FakeKeyRecords
from Security.application.EncryptionManager import EncryptionManager
from Security.application.KeyManager import KeyManager
from Security.domain.KeyRecord import KeyStatus
from Security.infrastructure.AesGcmCypher import AesGcmCypher
from Security.infrastructure.InMemoryResetConfirmations import InMemoryResetConfirmations

ALICE = "alice"
PASSPHRASE = "correct horse battery staple"
OTHER_PASSPHRASE = "a different passphrase"


@pytest.fixture
def cypher():
    return AesGcmCypher()


@pytest.fixture
def keyRecords():
    return FakeKeyRecords()


@pytest.fixture
def manager(keyRecords, cypher):
    return EncryptionManager(keyRecords, cypher, InMemoryResetConfirmations())


def confirm(manager, username=ALICE):
    code = manager.requestResetConfirmation(username)
    return code


# ---- Cypher: AES-GCM round trip -------------------------------------------------------------------------------

def test_cypher_round_trips_plaintext(cypher):
    key = cypher.generateDataKey()
    ciphertext = cypher.encrypt(b"hello world", key)
    assert ciphertext != b"hello world"
    assert cypher.decrypt(ciphertext, key) == b"hello world"


def test_cypher_decrypt_fails_with_the_wrong_key(cypher):
    key, wrongKey = cypher.generateDataKey(), cypher.generateDataKey()
    ciphertext = cypher.encrypt(b"secret", key)
    with pytest.raises(CorruptedDataError):
        cypher.decrypt(ciphertext, wrongKey)


def test_cypher_decrypt_fails_on_tampered_data(cypher):
    key = cypher.generateDataKey()
    ciphertext = bytearray(cypher.encrypt(b"secret", key))
    ciphertext[-1] ^= 0xFF
    with pytest.raises(CorruptedDataError):
        cypher.decrypt(bytes(ciphertext), key)


def test_cypher_wrapping_key_is_deterministic_for_the_same_secret_and_salt(cypher):
    salt = cypher.generateSalt()
    assert cypher.deriveWrappingKey(PASSPHRASE, salt) == cypher.deriveWrappingKey(PASSPHRASE, salt)
    assert cypher.deriveWrappingKey(PASSPHRASE, salt) != cypher.deriveWrappingKey(OTHER_PASSPHRASE, salt)


# ---- KeyManager: wrapping/unwrapping and rotation -------------------------------------------------------------

def test_key_manager_wraps_and_unwraps_the_same_data_key(cypher):
    km = KeyManager(cypher)
    record = km.generateKeyRecord(ALICE, PASSPHRASE)
    assert record.version == 1 and record.status == KeyStatus.ACTIVE
    dataKey = km.unwrapWithPassphrase(record, PASSPHRASE)
    assert len(dataKey) == 32


def test_key_manager_unwrap_fails_with_the_wrong_passphrase(cypher):
    km = KeyManager(cypher)
    record = km.generateKeyRecord(ALICE, PASSPHRASE)
    with pytest.raises(CorruptedDataError):
        km.unwrapWithPassphrase(record, OTHER_PASSPHRASE)


def test_key_manager_rotation_retires_the_previous_record_and_increments_version(cypher):
    km = KeyManager(cypher)
    first = km.generateKeyRecord(ALICE, PASSPHRASE)
    second = km.generateKeyRecord(ALICE, PASSPHRASE, previous=first)
    assert first.status == KeyStatus.RETIRED and first.retiredAt is not None
    assert second.version == 2 and second.status == KeyStatus.ACTIVE


def test_key_manager_rewrap_keeps_the_same_data_key(cypher):
    km = KeyManager(cypher)
    record = km.generateKeyRecord(ALICE, PASSPHRASE)
    dataKeyBefore = km.unwrapWithPassphrase(record, PASSPHRASE)
    km.rewrapWithNewPassphrase(record, PASSPHRASE, OTHER_PASSPHRASE)
    assert km.unwrapWithPassphrase(record, OTHER_PASSPHRASE) == dataKeyBefore
    with pytest.raises(CorruptedDataError):
        km.unwrapWithPassphrase(record, PASSPHRASE)  # the old passphrase no longer works


def test_key_manager_recovery_code_unwraps_the_same_data_key(cypher):
    km = KeyManager(cypher)
    record = km.generateKeyRecord(ALICE, PASSPHRASE)
    dataKeyBefore = km.unwrapWithPassphrase(record, PASSPHRASE)
    km.attachRecoveryCode(record, PASSPHRASE, "recovery-code-123")
    assert km.unwrapWithRecoveryCode(record, "recovery-code-123") == dataKeyBefore


def test_key_manager_recovery_code_missing_raises(cypher):
    km = KeyManager(cypher)
    record = km.generateKeyRecord(ALICE, PASSPHRASE)
    with pytest.raises(CorruptedDataError, match="No recovery code"):
        km.unwrapWithRecoveryCode(record, "anything")


# ---- EncryptionManager: content encryption --------------------------------------------------------------------

def test_encrypt_then_decrypt_content_round_trips(manager):
    keyVersion, ciphertext = manager.encryptContent(ALICE, PASSPHRASE, b"my secret diary entry")
    assert ciphertext != b"my secret diary entry"
    assert manager.decryptContent(ALICE, PASSPHRASE, keyVersion, ciphertext) == b"my secret diary entry"


def test_encrypt_creates_a_key_on_first_use_and_reuses_it_after(manager, keyRecords):
    manager.encryptContent(ALICE, PASSPHRASE, b"first")
    manager.encryptContent(ALICE, PASSPHRASE, b"second")
    assert len(keyRecords.getAll(ALICE)) == 1  # same KeyRecord reused, no duplicate created


def test_decrypt_fails_with_the_wrong_passphrase(manager):
    keyVersion, ciphertext = manager.encryptContent(ALICE, PASSPHRASE, b"my secret")
    with pytest.raises(CorruptedDataError):
        manager.decryptContent(ALICE, OTHER_PASSPHRASE, keyVersion, ciphertext)


def test_decrypt_with_an_unknown_key_version_raises(manager):
    with pytest.raises(CorruptedDataError, match="No key found"):
        manager.decryptContent(ALICE, PASSPHRASE, 99, b"garbage")


# ---- EncryptionManager: rotation -------------------------------------------------------------------------------

def test_rotate_key_creates_a_new_version_and_old_content_stays_readable_under_its_own_version(manager):
    oldVersion, ciphertext = manager.encryptContent(ALICE, PASSPHRASE, b"old content")
    newRecord = manager.rotateKey(ALICE, PASSPHRASE)
    assert newRecord.version == oldVersion + 1
    # Old content, still tagged with its original key version, is still decryptable.
    assert manager.decryptContent(ALICE, PASSPHRASE, oldVersion, ciphertext) == b"old content"
    # New content is now encrypted under the new, current key version.
    newVersion, _ = manager.encryptContent(ALICE, PASSPHRASE, b"new content")
    assert newVersion == newRecord.version


# ---- EncryptionManager: RQ4 confirmation gating the 3 reset cases -----------------------------------------------

def test_reset_without_a_confirmation_code_is_rejected(manager):
    manager.encryptContent(ALICE, PASSPHRASE, b"content")
    with pytest.raises(ValidationError, match="Request a confirmation code first"):
        manager.changePassphrase(ALICE, "000000", PASSPHRASE, OTHER_PASSPHRASE)


def test_reset_with_the_wrong_confirmation_code_is_rejected(manager):
    manager.encryptContent(ALICE, PASSPHRASE, b"content")
    code = confirm(manager)
    wrong = "000000" if code != "000000" else "111111"
    with pytest.raises(ValidationError, match="Wrong confirmation code"):
        manager.changePassphrase(ALICE, wrong, PASSPHRASE, OTHER_PASSPHRASE)


# ---- Case 1: know the current passphrase ------------------------------------------------------------------------

def test_case1_change_passphrase_keeps_content_decryptable(manager):
    keyVersion, ciphertext = manager.encryptContent(ALICE, PASSPHRASE, b"content")
    code = confirm(manager)
    manager.changePassphrase(ALICE, code, PASSPHRASE, OTHER_PASSPHRASE)
    assert manager.decryptContent(ALICE, OTHER_PASSPHRASE, keyVersion, ciphertext) == b"content"
    with pytest.raises(CorruptedDataError):
        manager.decryptContent(ALICE, PASSPHRASE, keyVersion, ciphertext)  # old passphrase no longer works


# ---- Case 1.B: recovery code set-up (not RQ4-gated: nothing is reset yet) ----------------------------------------

def test_generate_recovery_code_does_not_require_confirmation(manager):
    manager.encryptContent(ALICE, PASSPHRASE, b"content")
    recoveryCode = manager.generateRecoveryCode(ALICE, PASSPHRASE)
    assert recoveryCode


# ---- Case 2: recover with the recovery code -----------------------------------------------------------------------

def test_case2_recover_with_recovery_code_keeps_content_decryptable_and_is_one_time_use(manager):
    keyVersion, ciphertext = manager.encryptContent(ALICE, PASSPHRASE, b"content")
    recoveryCode = manager.generateRecoveryCode(ALICE, PASSPHRASE)

    code = confirm(manager)
    manager.recoverWithRecoveryCode(ALICE, code, recoveryCode, OTHER_PASSPHRASE)
    assert manager.decryptContent(ALICE, OTHER_PASSPHRASE, keyVersion, ciphertext) == b"content"

    # One-time use: the same recovery code cannot be used again.
    code2 = confirm(manager)
    with pytest.raises(CorruptedDataError, match="No recovery code"):
        manager.recoverWithRecoveryCode(ALICE, code2, recoveryCode, "yet another passphrase")


# ---- Case 3: wipe and reprovision (last resort) --------------------------------------------------------------------

def test_case3_wipe_and_reprovision_starts_a_brand_new_key_and_old_content_is_unrecoverable(manager, keyRecords):
    oldVersion, ciphertext = manager.encryptContent(ALICE, PASSPHRASE, b"content")
    code = confirm(manager)
    newRecord, recoveryCode = manager.wipeAndReprovision(ALICE, code, OTHER_PASSPHRASE)

    assert newRecord.version == 1  # a brand-new key history, not a continuation of the old one
    assert recoveryCode
    # The wipe discarded the old dataKey entirely -- even though the new history reuses version 1, it wraps
    # a completely different dataKey, so the old content's ciphertext no longer decrypts under it.
    with pytest.raises(CorruptedDataError):
        manager.decryptContent(ALICE, OTHER_PASSPHRASE, oldVersion, ciphertext)

    # The new passphrase works for new content right away.
    newVersion, newCiphertext = manager.encryptContent(ALICE, OTHER_PASSPHRASE, b"fresh start")
    assert manager.decryptContent(ALICE, OTHER_PASSPHRASE, newVersion, newCiphertext) == b"fresh start"


def test_case3_wipe_discards_every_previous_key_record(manager, keyRecords):
    manager.encryptContent(ALICE, PASSPHRASE, b"content")
    manager.rotateKey(ALICE, PASSPHRASE)  # now has key versions 1 (retired) and 2 (current)
    code = confirm(manager)
    manager.wipeAndReprovision(ALICE, code, OTHER_PASSPHRASE)
    assert [record.version for record in keyRecords.getAll(ALICE)] == [1]  # only the fresh key remains


def test_reset_on_a_user_with_no_key_yet_raises_not_found(manager):
    code = confirm(manager)
    with pytest.raises(NotFoundError):
        manager.changePassphrase(ALICE, code, PASSPHRASE, OTHER_PASSPHRASE)
