'''
AuthRoutes.py

HTTP routes for signing in:
    POST  /api/login               {username (or email), password}
    POST  /api/register            {username, email, password}   (also signs in)
    GET   /api/auth/google/start   redirects to Google ("Continue with Google")
    GET   /api/auth/google/callback  Google returns here; signs in and redirects to /
    POST  /api/logout
    GET   /api/me
Routes only translate HTTP to use-case calls and back; the rules live in the application layer.
'''
from typing import Optional
from urllib.parse import quote

from fastapi import APIRouter, Request, Response
from fastapi.responses import RedirectResponse

from CommonErrors.Errors import AppError, ExternalServiceError
from WI29_Server.application.AuthService import AuthService
from WI29_Server.application.GoogleSignIn import STATE_SECONDS, GoogleSignIn
from WI29_Server.interface.Schemas import LoginBody, RegisterBody
from WI29_Server.interface.Session import SESSION_COOKIE, isSecure, setSessionCookie

STATE_COOKIE = "google_oauth_state"
_STATE_COOKIE_PATH = "/api/auth/google"


def buildAuthRouter(auth: AuthService, google: GoogleSignIn, sessionSeconds: int) -> APIRouter:
    router = APIRouter()

    def startSession(request: Request, response: Response, token: str) -> dict:
        setSessionCookie(request, response, token, sessionSeconds)
        return {"username": auth.username(token)}

    @router.post("/api/login")
    def login(body: LoginBody, request: Request, response: Response):
        return startSession(request, response, auth.login(body.username, body.password))

    @router.post("/api/register")
    def register(body: RegisterBody, request: Request, response: Response):
        return startSession(request, response, auth.register(body.username, body.email, body.password))

    # "Continue with Google": /start sends the browser to Google, /callback is where Google sends it back.
    # Failures here go back to the page with a message instead of a JSON error, since the browser is navigating.
    def backWithError(message: str) -> RedirectResponse:
        result = RedirectResponse("/?auth_error=" + quote(message), status_code=303)
        result.delete_cookie(STATE_COOKIE, path=_STATE_COOKIE_PATH)
        return result

    @router.get("/api/auth/google/start")
    def googleStart(request: Request):
        if not google.configured:
            return backWithError("Google sign-in is not set up on this server.")
        scheme = request.headers.get("x-forwarded-proto") or request.url.scheme
        host = request.headers.get("x-forwarded-host") or request.headers.get("host") or request.url.netloc
        try:
            url, state = google.start(f"{scheme}://{host}/api/auth/google/callback")
        except AppError as failure:
            return backWithError(failure.message)
        response = RedirectResponse(url, status_code=303)
        response.set_cookie(STATE_COOKIE, state, max_age=STATE_SECONDS, httponly=True, samesite="lax",
                            secure=isSecure(request), path=_STATE_COOKIE_PATH)
        return response

    @router.get("/api/auth/google/callback")
    def googleCallback(request: Request, code: Optional[str] = None, state: Optional[str] = None,
                       error: Optional[str] = None):
        try:
            if error:
                raise ExternalServiceError("Google sign-in was cancelled.")
            profile = google.finish(state, request.cookies.get(STATE_COOKIE), code)
            token = auth.loginWithGoogle(profile)
        except AppError as failure:
            return backWithError(failure.message)
        response = RedirectResponse("/", status_code=303)
        response.delete_cookie(STATE_COOKIE, path=_STATE_COOKIE_PATH)
        startSession(request, response, token)
        return response

    @router.post("/api/logout")
    def logout(request: Request, response: Response):
        auth.logout(request.cookies.get(SESSION_COOKIE))
        response.delete_cookie(SESSION_COOKIE, path="/")
        return {"ok": True}

    @router.get("/api/me")
    def me(request: Request):
        return {"username": auth.username(request.cookies.get(SESSION_COOKIE))}

    return router
