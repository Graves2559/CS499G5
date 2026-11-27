'''
Schemas.py

Request bodies of the HTTP API (the shape and size limits of what clients send).
'''
from typing import Dict, Optional

from pydantic import BaseModel, Field


class LoginBody(BaseModel):
    username: str = Field(max_length=200)
    password: str = Field(max_length=500)


class RegisterBody(BaseModel):
    username: str = Field(max_length=64)
    email: str = Field(max_length=200)
    password: str = Field(max_length=200)


class FolderBody(BaseModel):
    id: str
    parentId: Optional[str] = None
    name: str = Field(max_length=120)
    description: str = Field(default="", max_length=300)


class EntryPatch(BaseModel):
    name: Optional[str] = Field(default=None, max_length=120)
    description: Optional[str] = Field(default=None, max_length=300)
    favorite: Optional[bool] = None


class EncryptChoiceBody(BaseModel):
    encryptChoice: bool


class SecurityQuestionsBody(BaseModel):
    questions: Dict[str, str] = Field(max_length=10)  # question -> answer


class ChangePassphraseBody(BaseModel):
    confirmationCode: str = Field(max_length=10)
    oldPassphrase: str = Field(max_length=500)
    newPassphrase: str = Field(max_length=500)
    securityAnswers: Optional[Dict[str, str]] = None


class GenerateRecoveryCodeBody(BaseModel):
    passphrase: str = Field(max_length=500)


class RecoverWithCodeBody(BaseModel):
    confirmationCode: str = Field(max_length=10)
    recoveryCode: str = Field(max_length=200)
    newPassphrase: str = Field(max_length=500)


class WipeAndReprovisionBody(BaseModel):
    confirmationCode: str = Field(max_length=10)
    newPassphrase: str = Field(max_length=500)


class RotateKeyBody(BaseModel):
    symmetricKey: str = Field(max_length=500)
