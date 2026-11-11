'''
Schemas.py

Request bodies of the HTTP API (the shape and size limits of what clients send).
'''
from typing import Optional

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
