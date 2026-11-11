'''
Policies.py

Domain rules for accounts: what a valid username, email and password look like. Pure functions, no I/O.
'''
import re

from CommonErrors.Errors import ValidationError

_USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9._-]{3,32}$")
_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_MAX_EMAIL_LENGTH = 200


def checkPasswordStrength(password: str) -> bool:
    # At least 8 characters, with an uppercase letter, a lowercase letter, a digit, and a special character
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(not c.isalnum() for c in password)
    return len(password) >= 8 and has_upper and has_lower and has_digit and has_special


def requireStrongPassword(password: str):
    if not checkPasswordStrength(password):
        raise ValidationError("Password does not meet strength requirements.")


def requireValidUsername(username: str):
    if not _USERNAME_PATTERN.match(username):
        raise ValidationError("Username must be 3-32 characters: letters, numbers, dot, dash or underscore.")


def requireValidEmail(email: str):
    if not _EMAIL_PATTERN.match(email) or len(email) > _MAX_EMAIL_LENGTH:
        raise ValidationError("Enter a valid email address.")


# Base for a username made from a Google profile: only allowed characters, 3-24 long.
def usernameBase(name: str, email: str) -> str:
    base = re.sub(r"[^A-Za-z0-9._-]", "", name) or re.sub(r"[^A-Za-z0-9._-]", "", email.split("@")[0]) or "user"
    return (base + "user")[:24] if len(base) < 3 else base[:24]
