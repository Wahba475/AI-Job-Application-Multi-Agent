"""Auth CONTROLLER — thin request handlers.

Parse/validate the request, call the service, shape the response.
No business logic here — that lives in services/auth_service.py.
"""
from fastapi import Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field

from services.auth_service import AuthError, login_user, register_user
from middleware.auth_middleware import get_current_user


# ── Request bodies ──────────────────────────────────────────────────────────

class RegisterBody(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    name: str | None = None


class LoginBody(BaseModel):
    email: EmailStr
    password: str


# ── Handlers ────────────────────────────────────────────────────────────────

async def register(body: RegisterBody):
    try:
        return register_user(body.email, body.password, body.name)
    except AuthError as e:
        raise HTTPException(status_code=e.status, detail=e.message)


async def login(body: LoginBody):
    try:
        return login_user(body.email, body.password)
    except AuthError as e:
        raise HTTPException(status_code=e.status, detail=e.message)


async def me(user: dict = Depends(get_current_user)):
    """Return the caller's identity from their token (protected route)."""
    return user
