'''
AuthRoutes.py

HTTP routes for signing in:
    POST  /api/login      {username (or email), password}
    POST  /api/register   {username, email, password}   (also signs in)
    POST  /api/logout
    GET   /api/me
Routes only translate HTTP to use-case calls and back; the rules live in the application layer.

# RQ2 (Security/README.md): there is no Google sign-in. Every account signs in with its own password.
'''
from fastapi import APIRouter, Request, Response

from WI29_Server.application.AuthService import AuthService
from WI29_Server.interface.Schemas import LoginBody, RegisterBody
from WI29_Server.interface.Session import SESSION_COOKIE, setSessionCookie


def buildAuthRouter(auth: AuthService, sessionSeconds: int) -> APIRouter:
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

    @router.post("/api/logout")
    def logout(request: Request, response: Response):
        auth.logout(request.cookies.get(SESSION_COOKIE))
        response.delete_cookie(SESSION_COOKIE, path="/")
        return {"ok": True}

    @router.get("/api/me")
    def me(request: Request):
        return {"username": auth.username(request.cookies.get(SESSION_COOKIE))}

    return router
