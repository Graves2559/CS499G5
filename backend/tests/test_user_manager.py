from datetime import datetime, timedelta, timezone

import pytest

from CommonErrors.Errors import ConflictError, UnauthorizedError, ValidationError
from Fakes import FakeHasher, FakeUsers
from UserLogin.application.UserManager import UserManager
from UserLogin.domain.User import User

STRONG = "Str0ng#Pass"


@pytest.fixture
def users():
    return FakeUsers()


@pytest.fixture
def hasher():
    return FakeHasher()


@pytest.fixture
def manager(users, hasher):
    return UserManager(users, hasher)


def test_register_stores_the_account_with_a_password_hash(manager, users):
    user = manager.registerUser("alice", "alice@example.com", STRONG)
    assert user.hasPassword()
    assert users.get("alice") is user


@pytest.mark.parametrize("username,email,message", [
    ("a b", "x@example.com", "Username must be"),
    ("ab", "x@example.com", "Username must be"),
    ("alice", "not-an-email", "valid email"),
])
def test_register_rejects_malformed_input(manager, username, email, message):
    with pytest.raises(ValidationError, match=message):
        manager.registerUser(username, email, STRONG)


def test_register_rejects_weak_password(manager):
    with pytest.raises(ValidationError, match="strength"):
        manager.registerUser("alice", "alice@example.com", "weak")


def test_register_rejects_duplicates_ignoring_case(manager):
    manager.registerUser("alice", "alice@example.com", STRONG)
    with pytest.raises(ConflictError, match="Username already exists"):
        manager.registerUser("ALICE", "other@example.com", STRONG)
    with pytest.raises(ConflictError, match="already in use"):
        manager.registerUser("alice2", "Alice@Example.com", STRONG)


def test_authenticate_by_username_or_email(manager):
    manager.registerUser("alice", "alice@example.com", STRONG)
    assert manager.authenticateUser("alice", STRONG).getUsername() == "alice"
    assert manager.authenticateUser("ALICE@example.com", STRONG).getUsername() == "alice"


def test_authenticate_fails_the_same_way_for_wrong_password_and_unknown_user(manager, hasher):
    manager.registerUser("alice", "alice@example.com", STRONG)
    hasher.verifyCalls = 0
    assert manager.authenticateUser("alice", "wrong") is None
    assert manager.authenticateUser("nobody", "wrong") is None
    assert hasher.verifyCalls == 2  # an unknown user costs a hash check too, so timing does not reveal accounts


def test_seed_user_skips_password_rule_and_is_idempotent(manager, users):
    manager.seedUser("adminUsername", "admin@example.com", "password")
    manager.seedUser("adminUsername", "admin@example.com", "different")
    assert manager.authenticateUser("adminUsername", "password") is not None
    assert len(users.users) == 1


def test_edit_password_requires_current_and_strong_new(manager):
    user = manager.registerUser("alice", "alice@example.com", STRONG)
    with pytest.raises(UnauthorizedError):
        manager.editUserPassword(user, "wrong", "N3w#Password")
    with pytest.raises(ValidationError):
        manager.editUserPassword(user, STRONG, "weak")
    manager.editUserPassword(user, STRONG, "N3w#Password")
    assert manager.authenticateUser("alice", "N3w#Password") is not None
    assert manager.authenticateUser("alice", STRONG) is None


def test_email_is_bound_only_when_the_code_is_correct(manager):
    user = manager.registerUser("alice", "alice@example.com", STRONG)
    code = manager.requestEmailVerification(user, "alice@gmail.com")
    assert user.getEmail() == "alice@example.com"
    manager.verifyEmail(user, code)
    assert user.getEmail() == "alice@gmail.com" and user.getPendingEmail() is None


def test_wrong_code_reports_an_error_and_does_not_bind(manager):
    user = manager.registerUser("alice", "alice@example.com", STRONG)
    code = manager.requestEmailVerification(user, "alice@gmail.com")
    wrong = "000000" if code != "000000" else "111111"
    with pytest.raises(ValidationError, match="Wrong verification code"):
        manager.verifyEmail(user, wrong)
    assert user.getEmail() == "alice@example.com"
    manager.verifyEmail(user, code)
    assert user.getEmail() == "alice@gmail.com"


def test_code_is_discarded_after_too_many_wrong_guesses(manager):
    user = manager.registerUser("alice", "alice@example.com", STRONG)
    code = manager.requestEmailVerification(user, "alice@gmail.com")
    wrong = "000000" if code != "000000" else "111111"
    for _ in range(5):
        with pytest.raises(ValidationError, match="Wrong verification code"):
            manager.verifyEmail(user, wrong)
    with pytest.raises(ValidationError, match="No email is waiting"):
        manager.verifyEmail(user, code)


def test_expired_code_is_rejected():
    user = User("alice", "alice@example.com")
    now = datetime.now(timezone.utc)
    code = user.requestEmailVerification("alice@gmail.com", now)
    with pytest.raises(ValidationError, match="expired"):
        user.verifyEmail(code, now + timedelta(minutes=11))
    assert user.getEmail() == "alice@example.com"


def test_cannot_start_binding_an_email_used_by_another_account(manager):
    manager.registerUser("bob", "bob@gmail.com", STRONG)
    user = manager.registerUser("alice", "alice@example.com", STRONG)
    with pytest.raises(ConflictError):
        manager.requestEmailVerification(user, "bob@gmail.com")


def test_security_questions_are_verified_case_and_whitespace_insensitively(manager):
    user = manager.registerUser("alice", "alice@example.com", STRONG)
    manager.setupSecurityQuestions(user, {"First pet?": "Rex", "Favorite color?": "Blue"})
    assert manager.verifySecurityAnswers(user, {"First pet?": "  rex ", "Favorite color?": "BLUE"})


def test_security_questions_reject_a_wrong_or_missing_answer(manager):
    user = manager.registerUser("alice", "alice@example.com", STRONG)
    manager.setupSecurityQuestions(user, {"First pet?": "Rex", "Favorite color?": "Blue"})
    assert not manager.verifySecurityAnswers(user, {"First pet?": "Rex", "Favorite color?": "Green"})
    assert not manager.verifySecurityAnswers(user, {"First pet?": "Rex"})  # missing the second question


def test_no_security_questions_configured_vacuously_verifies(manager):
    user = manager.registerUser("alice", "alice@example.com", STRONG)
    assert manager.verifySecurityAnswers(user, {})


def test_setup_security_questions_requires_at_least_one(manager):
    user = manager.registerUser("alice", "alice@example.com", STRONG)
    with pytest.raises(ValidationError, match="At least one security question"):
        manager.setupSecurityQuestions(user, {})


def test_setup_security_questions_replaces_the_previous_set(manager):
    user = manager.registerUser("alice", "alice@example.com", STRONG)
    manager.setupSecurityQuestions(user, {"First pet?": "Rex"})
    manager.setupSecurityQuestions(user, {"Favorite color?": "Blue"})
    assert list(user.getSecurityQuestions().keys()) == ["Favorite color?"]
