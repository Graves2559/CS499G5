'''
Session.py

HTTP details of the session cookie, and the dependency that turns it into the signed-in username.
'''
from fastapi import Request, Response

from CommonErrors.Errors import UnauthorizedError
from WI29_Server.application.AuthService import AuthService

SESSION_COOKIE = "session"


def isSecure(request: Request) -> bool:
    return request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https"


def setSessionCookie(request: Request, response: Response, token: str, maxAge: int):
    response.set_cookie(SESSION_COOKIE, token, max_age=maxAge, httponly=True, samesite="lax",
                        secure=isSecure(request), path="/")


def makeCurrentUser(auth: AuthService):
    def currentUser(request: Request) -> str:
        username = auth.username(request.cookies.get(SESSION_COOKIE))
        if username is None:
            raise UnauthorizedError("Please sign in.")
        return username
    return currentUser
