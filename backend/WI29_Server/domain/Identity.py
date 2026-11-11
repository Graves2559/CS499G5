'''
Identity.py

Domain value: the profile an identity provider (Google) vouches for.
'''
from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderProfile:
    subject: str          # the provider's stable id for the account ("sub")
    email: str
    emailVerified: bool
    name: str
