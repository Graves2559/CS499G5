'''
GoogleIdentityProvider.py

Implements the IdentityProvider port against Google's OAuth 2.0 / OpenID Connect endpoints (found through Google's
discovery document). Every HTTP call has a timeout.
'''
import threading
import time
from typing import Optional
from urllib.parse import urlencode

import requests

from CommonErrors.Errors import ExternalServiceError
from WI29_Server.domain.Identity import ProviderProfile

_DISCOVERY_SECONDS = 3600
_HTTP_TIMEOUT = 10


class GoogleIdentityProvider:
    def __init__(self, clientId: Optional[str], clientSecret: Optional[str], discoveryUrl: str):
        self.clientId = clientId
        self.clientSecret = clientSecret
        self.discoveryUrl = discoveryUrl
        self._config = None
        self._configTime = 0.0
        self._lock = threading.Lock()

    @property
    def configured(self) -> bool:
        return bool(self.clientId and self.clientSecret)

    # Google's endpoints come from its discovery document (cached for an hour).
    def _providerConfig(self) -> dict:
        now = time.time()
        with self._lock:
            if self._config is not None and now - self._configTime < _DISCOVERY_SECONDS:
                return self._config
        try:
            config = requests.get(self.discoveryUrl, timeout=_HTTP_TIMEOUT).json()
            config["authorization_endpoint"], config["token_endpoint"], config["userinfo_endpoint"]
        except Exception:
            raise ExternalServiceError("Could not reach Google. Please try again.")
        with self._lock:
            self._config, self._configTime = config, now
        return config

    def authorizationUrl(self, redirectUri: str, state: str, codeChallenge: str) -> str:
        query = urlencode({
            "client_id": self.clientId,
            "redirect_uri": redirectUri,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "code_challenge": codeChallenge,
            "code_challenge_method": "S256",
            "prompt": "select_account",
        })
        return f"{self._providerConfig()['authorization_endpoint']}?{query}"

    def fetchProfile(self, code: str, redirectUri: str, codeVerifier: str) -> ProviderProfile:
        config = self._providerConfig()
        try:
            token = requests.post(config["token_endpoint"], timeout=_HTTP_TIMEOUT, data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirectUri,
                "client_id": self.clientId,
                "client_secret": self.clientSecret,
                "code_verifier": codeVerifier,
            })
            accessToken = token.json().get("access_token") if token.ok else None
            if not accessToken:
                # Logged for the person running the server (never includes the secret or the code)
                try:
                    reason = token.json().get("error_description") or token.json().get("error")
                except ValueError:
                    reason = "unreadable response"
                print(f"Google token exchange failed ({token.status_code}): {reason}", flush=True)
                raise ExternalServiceError("Google sign-in failed. Please try again.")
            info = requests.get(config["userinfo_endpoint"], timeout=_HTTP_TIMEOUT,
                                headers={"Authorization": f"Bearer {accessToken}"}).json()
        except requests.RequestException:
            raise ExternalServiceError("Could not reach Google. Please try again.")
        return ProviderProfile(
            subject=str(info.get("sub") or ""),
            email=info.get("email") or "",
            emailVerified=info.get("email_verified") is True,
            name=info.get("given_name") or info.get("name") or "",
        )
