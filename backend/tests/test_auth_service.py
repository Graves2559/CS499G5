import pytest

from CommonErrors.Errors import TooManyRequestsError, UnauthorizedError
from Fakes import Clock, FakeHasher, FakeUsers
from UserLogin.application.UserManager import UserManager
from WI29_Server.application.AuthService import AuthService
from WI29_Server.domain.Identity import ProviderProfile
from WI29_Server.infrastructure.MemoryStores import InMemorySessionStore, SlidingWindowLimiter

STRONG = "Str0ng#Pass"


@pytest.fixture
def clock():
    return Clock()


@pytest.fixture
def auth(clock):
    return AuthService(
        UserManager(FakeUsers(), FakeHasher()),
        InMemorySessionStore(3600, clock),
        SlidingWindowLimiter(5, 60, clock=clock),
        SlidingWindowLimiter(2, 60, clock=clock),
    )


def test_register_signs_in(auth):
    token = auth.register(" alice ", " alice@example.com ", STRONG)
    assert auth.username(token) == "alice"


def test_login_with_username_or_email(auth):
    auth.register("alice", "alice@example.com", STRONG)
    assert auth.username(auth.login("alice", STRONG)) == "alice"
    assert auth.username(auth.login("alice@example.com", STRONG)) == "alice"


def test_wrong_password_is_unauthorized_and_unknown_user_looks_the_same(auth):
    auth.register("alice", "alice@example.com", STRONG)
    for who in ("alice", "nobody"):
        with pytest.raises(UnauthorizedError, match="Incorrect username or password"):
            auth.login(who, "wrong")


def test_login_is_throttled_after_five_failures_and_recovers(auth, clock):
    auth.register("alice", "alice@example.com", STRONG)
    for _ in range(5):
        with pytest.raises(UnauthorizedError):
            auth.login("alice", "wrong")
    with pytest.raises(TooManyRequestsError):
        auth.login("alice", STRONG)  # even the right password is refused while throttled
    clock.now += 61
    assert auth.username(auth.login("alice", STRONG)) == "alice"


def test_a_successful_login_resets_the_failures(auth):
    auth.register("alice", "alice@example.com", STRONG)
    for _ in range(4):
        with pytest.raises(UnauthorizedError):
            auth.login("alice", "wrong")
    auth.login("alice", STRONG)
    for _ in range(4):
        with pytest.raises(UnauthorizedError):
            auth.login("alice", "wrong")  # would be throttled by now if the counter had not been reset


def test_registrations_are_limited(auth):
    auth.register("alice", "alice@example.com", STRONG)
    auth.register("bobby", "bobby@example.com", STRONG)
    with pytest.raises(TooManyRequestsError):
        auth.register("carol", "carol@example.com", STRONG)


def test_invalid_registrations_do_not_use_up_the_limit(auth):
    for _ in range(5):
        with pytest.raises(Exception):
            auth.register("a b", "bad", STRONG)
    auth.register("alice", "alice@example.com", STRONG)


def test_sessions_expire_and_logout_ends_them(auth, clock):
    token = auth.register("alice", "alice@example.com", STRONG)
    auth.logout(token)
    assert auth.username(token) is None
    token = auth.login("alice", STRONG)
    clock.now += 3601
    assert auth.username(token) is None


def test_unknown_or_missing_token(auth):
    assert auth.username(None) is None
    assert auth.username("nope") is None


def test_login_with_google(auth):
    token = auth.loginWithGoogle(ProviderProfile("g-1", "dana@example.com", True, "Dana"))
    assert auth.username(token) == "Dana"


def test_every_way_of_signing_in_runs_the_on_signed_in_hook(clock):
    seen = []
    svc = AuthService(
        UserManager(FakeUsers(), FakeHasher()), InMemorySessionStore(3600, clock),
        SlidingWindowLimiter(5, 60, clock=clock), SlidingWindowLimiter(5, 60, clock=clock),
        onSignedIn=seen.append,
    )
    svc.register("alice", "alice@example.com", STRONG)
    svc.login("alice", STRONG)
    svc.loginWithGoogle(ProviderProfile("g-1", "dana@example.com", True, "Dana"))
    assert seen == ["alice", "alice", "Dana"]


def test_a_failed_login_does_not_run_the_hook(clock):
    seen = []
    svc = AuthService(
        UserManager(FakeUsers(), FakeHasher()), InMemorySessionStore(3600, clock),
        SlidingWindowLimiter(5, 60, clock=clock), SlidingWindowLimiter(5, 60, clock=clock),
        onSignedIn=seen.append,
    )
    with pytest.raises(UnauthorizedError):
        svc.login("nobody", "x")
    assert seen == []
