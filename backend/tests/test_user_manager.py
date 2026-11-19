import pytest

from CommonErrors.Errors import ConflictError, UnauthorizedError, ValidationError
from Fakes import FakeHasher, FakeUsers
from UserLogin.application.UserManager import UserManager

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


def test_google_only_account_cannot_sign_in_with_a_password(manager):
    manager.signInWithGoogle("g-1", "dana@example.com", "Dana")
    assert manager.authenticateUser("Dana", "") is None


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


def test_google_sign_in_creates_then_reuses_the_account(manager, users):
    first = manager.signInWithGoogle("g-1", "dana@example.com", "Dana")
    assert first == "Dana" and users.get("Dana").getEmail() == "dana@example.com"
    assert manager.signInWithGoogle("g-1", "dana@example.com", "Dana") == "Dana"
    assert len(users.users) == 1


def test_google_sign_in_never_links_to_an_existing_password_account(manager):
    manager.registerUser("alice", "alice@example.com", STRONG)
    with pytest.raises(ConflictError, match="already exists"):
        manager.signInWithGoogle("g-9", "alice@example.com", "Alice")


def test_google_username_clash_gets_a_unique_name(manager):
    manager.registerUser("Dana", "someone@example.com", STRONG)
    username = manager.signInWithGoogle("g-2", "dana2@example.com", "Dana")
    assert username != "Dana" and username.startswith("Dana")
