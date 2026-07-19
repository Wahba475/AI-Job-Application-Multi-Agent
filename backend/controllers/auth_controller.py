"""Auth CONTROLLER — thin request handlers (same role as your Node controllers).
Parse/validate the request, call the service, shape the response. No business
logic here — that lives in services/auth_service.py.
"""
from backend.services import auth_service
from fastapi import HTTPException, Depends
from pydantic import BaseModel, EmailStr, Field

from services.auth_service import register_user, login_user, AuthError
from middleware.auth_middleware import get_current_user


# ── request bodies (validation, like express-validator) ────
class RegisterBody(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    name: str | None = None


class LoginBody(BaseModel):
    email: EmailStr
    password: str


# ── handlers ───────────────────────────────────────────────
async def register(body: RegisterBody):
    try:
        return auth_service.register_user(body.email, body.password, body.name)
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
