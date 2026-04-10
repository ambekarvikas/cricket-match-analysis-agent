from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    email: str
    password: str = Field(min_length=8)
    display_name: Optional[str] = Field(default=None, max_length=120)


class LoginRequest(BaseModel):
    email: str
    password: str = Field(min_length=8)


class AuthUser(BaseModel):
    id: int
    email: str
    display_name: Optional[str] = None
    created_at: Optional[str] = None


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: AuthUser
