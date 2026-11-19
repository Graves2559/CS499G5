from WI29_Server.domain.Files import detectContentType, requireValidId, requireValidName
from CommonErrors.Errors import ValidationError
import pytest


def test_content_type_comes_from_the_bytes():
    assert detectContentType(b"\x89PNG\r\n\x1a\nrest") == "image/png"
    assert detectContentType(b"\xff\xd8\xffdata") == "image/jpeg"
    assert detectContentType(b"%PDF-1.7 ...") == "application/pdf"
    assert detectContentType("héllo".encode()) == "text/plain"
    assert detectContentType(b"") == "text/plain"


def test_binary_and_invalid_text_are_unsupported():
    assert detectContentType(b"MZ\x00\x01") is None
    assert detectContentType(b"\xff\xfe\xfa") is None


@pytest.mark.parametrize("value", ["", "has space", "a/b", "x" * 65, "é"])
def test_invalid_ids(value):
    with pytest.raises(ValidationError):
        requireValidId(value)


@pytest.mark.parametrize("value", ["", "   ", "a/b", "a\\b", "x" * 121])
def test_invalid_names(value):
    with pytest.raises(ValidationError):
        requireValidName(value)


def test_valid_id_and_name():
    requireValidId("0ce83534-b63d-4f87-8d42-38e67ecc1e7e")
    requireValidName("Screenshot 2026-08-02 225417.png")
