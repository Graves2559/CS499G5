'''
Files.py

Domain model and rules for a user's folders and files. Pure Python: no database, web framework or I/O.
'''
import re
from dataclasses import dataclass
from typing import Optional

from CommonErrors.Errors import ValidationError

MAX_FILE_BYTES = 25 * 1024 * 1024
MAX_NAME_LENGTH = 120
MAX_DESCRIPTION_LENGTH = 300

# The Input and Output folders exist for every user and their names are fixed.
PROTECTED_FOLDERS = {"input": "Input", "output": "Output"}
DEFAULT_FOLDERS = {
    "input": ("Input", "Uploaded files and source text"),
    "output": ("Output", "Files and text after Run"),
}

_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
_SIGNATURES = (("image/png", b"\x89PNG\r\n\x1a\n"), ("image/jpeg", b"\xff\xd8\xff"), ("application/pdf", b"%PDF-"))


@dataclass(frozen=True)
class Folder:
    id: str
    parentId: Optional[str]
    name: str
    description: str = ""


@dataclass(frozen=True)
class FileEntry:
    id: str
    parentId: Optional[str]
    name: str
    description: str = ""
    contentType: Optional[str] = None
    size: Optional[int] = None
    favorite: bool = False
    dateModified: Optional[str] = None
    mediaId: Optional[str] = None  # where the content lives in the content store; never sent to clients


def requireValidId(value: str):
    if not value or not _ID_PATTERN.match(value):
        raise ValidationError("Invalid id.")


def requireValidName(name: str):
    if not name or not name.strip() or "/" in name or "\\" in name or len(name) > MAX_NAME_LENGTH:
        raise ValidationError("Enter a name without slashes (up to 120 characters).")


# The content type is decided from the bytes, never from what the client claims. Returns None if unsupported.
def detectContentType(content: bytes) -> Optional[str]:
    for contentType, signature in _SIGNATURES:
        if content.startswith(signature):
            return contentType
    if b"\x00" in content:
        return None
    try:
        content.decode("utf-8")
    except UnicodeDecodeError:
        return None
    return "text/plain"
