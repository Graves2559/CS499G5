'''
GoogleSignIn.py

"Continue with Google" (OAuth 2.0 authorization code flow), following the LowCloud client's login/callback
routes (CyberProjects/Docker/lowcloudclient/client.py) with these differences:
- a random `state` is bound to the browser by a cookie, and PKCE is used (the reference has neither),
- every login attempt keeps its own state (the reference shares one OAuth client object between users),
- the redirect URI is configurable.

This class holds the flow's rules; talking to Google is the IdentityProvider port's job.
'''
import base64
import hashlib
import secrets
from typing import Optional, Tuple

from CommonErrors.Errors import ExternalServiceError
from WI29_Server.application.Ports import IdentityProvider, PendingLogins
from WI29_Server.domain.Identity import ProviderProfile

STATE_SECONDS = 600


class GoogleSignIn:
    def __init__(self, provider: IdentityProvider, pending: PendingLogins, redirectUriOverride: Optional[str] = None):
        self.provider = provider
        self.pending = pending
        self.redirectUriOverride = redirectUriOverride

    @property
    def configured(self) -> bool:
        return self.provider.configured

    # Returns (the Google URL to send the browser to, the state to store in the browser's cookie).
    def start(self, defaultRedirectUri: str) -> Tuple[str, str]:
        redirectUri = self.redirectUriOverride or defaultRedirectUri
        state = secrets.token_urlsafe(32)
        verifier = secrets.token_urlsafe(64)
        challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
        if not self.pending.add(state, verifier, redirectUri):
            raise ExternalServiceError("Too many sign-in attempts. Try again in a few minutes.")
        return self.provider.authorizationUrl(redirectUri, state, challenge), state

    # Exchanges the code for the user's verified Google profile. Raises ExternalServiceError.
    def finish(self, state: Optional[str], cookieState: Optional[str], code: Optional[str]) -> ProviderProfile:
        if not state or not cookieState or not secrets.compare_digest(state, cookieState):
            raise ExternalServiceError("Sign-in expired or was started in another browser. Please try again.")
        pending = self.pending.pop(state)
        if pending is None:
            raise ExternalServiceError("Sign-in expired. Please try again.")
        verifier, redirectUri = pending
        if not code:
            raise ExternalServiceError("Google did not return a sign-in code.")
        profile = self.provider.fetchProfile(code, redirectUri, verifier)
        # Same rule as the reference: the email must be verified by Google.
        if not profile.subject or not profile.email or profile.emailVerified is not True:
            raise ExternalServiceError("Google did not provide a verified email address.")
        return profile
