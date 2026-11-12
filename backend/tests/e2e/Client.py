'''
Client.py

A tiny HTTP client for the end-to-end tests, using only the standard library. It keeps the session cookie, like a
browser does, and talks to the running app (default http://localhost:8000, override with E2E_BASE_URL).
'''
import http.cookiejar
import json
import os
import urllib.error
import urllib.parse
import urllib.request
import uuid
from dataclasses import dataclass

BASE_URL = os.environ.get("E2E_BASE_URL", "http://localhost:8000")


@dataclass
class Response:
    status: int
    body: bytes
    headers: dict

    def json(self):
        return json.loads(self.body)

    @property
    def detail(self) -> str:
        return self.json().get("detail", "")


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def _id(entryId: str) -> str:
    return urllib.parse.quote(entryId, safe="")  # like encodeURIComponent in the browser


def _multipart(fields: dict, filename: str, content: bytes):
    boundary = uuid.uuid4().hex
    parts = []
    for key, value in fields.items():
        parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"\r\n\r\n{value}\r\n'.encode())
    parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{filename}"\r\n'
                 f"Content-Type: application/octet-stream\r\n\r\n".encode() + content + b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode())
    return b"".join(parts), f"multipart/form-data; boundary={boundary}"


class Client:
    def __init__(self, base: str = BASE_URL):
        self.base = base
        self.jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar), _NoRedirect)

    def request(self, method: str, path: str, payload=None, body: bytes = None, contentType: str = None) -> Response:
        headers = {}
        if payload is not None:
            body, contentType = json.dumps(payload).encode(), "application/json"
        if contentType:
            headers["Content-Type"] = contentType
        request = urllib.request.Request(self.base + path, data=body, method=method, headers=headers)
        try:
            with self.opener.open(request, timeout=60) as response:
                return Response(response.status, response.read(), dict(response.headers))
        except urllib.error.HTTPError as error:
            return Response(error.code, error.read(), dict(error.headers))

    # --- the API, one method per endpoint --------------------------------------------------------------------

    def register(self, username: str, email: str, password: str) -> Response:
        return self.request("POST", "/api/register", {"username": username, "email": email, "password": password})

    def login(self, username: str, password: str) -> Response:
        return self.request("POST", "/api/login", {"username": username, "password": password})

    def entries(self) -> Response:
        return self.request("GET", "/api/entries")

    def upload(self, entryId: str, name: str, content: bytes, parentId: str = "input", description: str = "") -> Response:
        body, contentType = _multipart({"parentId": parentId, "name": name, "description": description}, name, content)
        return self.request("PUT", f"/api/files/{_id(entryId)}", body=body, contentType=contentType)

    def download(self, entryId: str) -> Response:
        return self.request("GET", f"/api/files/{_id(entryId)}/content")

    def update(self, entryId: str, changes: dict) -> Response:
        return self.request("PATCH", f"/api/entries/{_id(entryId)}", changes)

    def names(self) -> list:
        return sorted(entry["name"] for entry in self.entries().json())

    def setSessionCookie(self, value: str):
        self.jar.set_cookie(http.cookiejar.Cookie(
            0, "session", value, None, False, "localhost", True, False, "/", True, False, None, False, None, None, {}))
