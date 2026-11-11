import base64
import hashlib

import pytest

from CommonErrors.Errors import ExternalServiceError
from Fakes import Clock, FakeProvider
from WI29_Server.application.GoogleSignIn import GoogleSignIn
from WI29_Server.domain.Identity import ProviderProfile
from WI29_Server.infrastructure.MemoryStores import InMemoryPendingLogins

PROFILE = ProviderProfile("g-1", "dana@example.com", True, "Dana")
DEFAULT_REDIRECT = "http://localhost:8000/api/auth/google/callback"


def flow(profile=PROFILE, override=None, capacity=1000, clock=None):
    provider = FakeProvider(profile)
    pending = InMemoryPendingLogins(600, capacity, clock or Clock())
    return GoogleSignIn(provider, pending, override), provider


def startedState(signIn):
    url, state = signIn.start(DEFAULT_REDIRECT)
    return url, state


def test_start_uses_state_and_a_pkce_challenge():
    signIn, provider = flow()
    url, state = startedState(signIn)
    assert f"state={state}" in url and len(state) >= 32
    verifier = signIn.pending.pop(state)[0]
    expected = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    assert f"challenge={expected}" in url


def test_finish_returns_the_profile_and_sends_the_verifier():
    signIn, provider = flow()
    _, state = startedState(signIn)
    assert signIn.finish(state, state, "code") == PROFILE
    assert provider.lastCodeVerifier


def test_redirect_override_wins():
    signIn, _ = flow(override="https://example.com/cb")
    url, state = startedState(signIn)
    assert "redirect=https://example.com/cb" in url


def test_callback_must_come_from_the_browser_that_started_the_sign_in():
    signIn, _ = flow()
    _, state = startedState(signIn)
    with pytest.raises(ExternalServiceError, match="another browser"):
        signIn.finish(state, None, "code")
    with pytest.raises(ExternalServiceError, match="another browser"):
        signIn.finish(state, "forged", "code")


def test_forged_state_is_rejected():
    signIn, _ = flow()
    with pytest.raises(ExternalServiceError, match="expired"):
        signIn.finish("forged", "forged", "code")


def test_state_is_single_use():
    signIn, _ = flow()
    _, state = startedState(signIn)
    signIn.finish(state, state, "code")
    with pytest.raises(ExternalServiceError, match="expired"):
        signIn.finish(state, state, "code")


def test_state_expires():
    clock = Clock()
    signIn, _ = flow(clock=clock)
    _, state = startedState(signIn)
    clock.now += 601
    with pytest.raises(ExternalServiceError, match="expired"):
        signIn.finish(state, state, "code")


def test_missing_code():
    signIn, _ = flow()
    _, state = startedState(signIn)
    with pytest.raises(ExternalServiceError, match="code"):
        signIn.finish(state, state, "")


@pytest.mark.parametrize("profile", [
    ProviderProfile("g-1", "dana@example.com", False, "Dana"),
    ProviderProfile("g-1", "", True, "Dana"),
    ProviderProfile("", "dana@example.com", True, "Dana"),
])
def test_only_verified_emails_are_accepted(profile):
    signIn, _ = flow(profile)
    _, state = startedState(signIn)
    with pytest.raises(ExternalServiceError, match="verified email"):
        signIn.finish(state, state, "code")


def test_too_many_pending_sign_ins():
    signIn, _ = flow(capacity=2)
    startedState(signIn)
    startedState(signIn)
    with pytest.raises(ExternalServiceError, match="Too many"):
        startedState(signIn)
