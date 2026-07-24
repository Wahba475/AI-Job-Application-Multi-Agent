"""Auth SERVICE layer — all the business logic (same role as a service file in
your MERN backend). Password hashing, JWT signing/verifying, and the actual
register/login work against the Supabase `users` table.

Controllers call these functions; they don't touch bcrypt/JWT/DB directly.
"""
import os
import datetime as dt

import bcrypt
from jose import jwt, JWTError

from db.supabase_client import get_supabase

# bcrypt directly — passlib+bcrypt>=4.1 crashes on backend init (72-byte probe).
_ALGO = "HS256"
_TOKEN_TTL_HOURS = 24 * 7  # token valid for 1 week


# ── password + token primitives ────────────────────────────
def hash_password(password: str) -> str:
    # bcrypt hard-caps at 72 bytes
    raw = password.encode("utf-8")[:72]
    return bcrypt.hashpw(raw, bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    raw = password.encode("utf-8")[:72]
    try:
        return bcrypt.checkpw(raw, password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def _secret() -> str:
    secret = os.getenv("JWT_SECRET")
    if not secret:
        raise RuntimeError("JWT_SECRET not set in .env")
    return secret


def create_token(user_id: str, email: str) -> str:
    """Sign a JWT carrying the user id (`sub`) + email, expiring in a week.
    Same idea as jsonwebtoken.sign({ id }, secret, { expiresIn })."""
    now = dt.datetime.now(dt.timezone.utc)
    payload = {
        "sub": str(user_id),
        "email": email,
        "iat": now,
        "exp": now + dt.timedelta(hours=_TOKEN_TTL_HOURS),
    }
    return jwt.encode(payload, _secret(), algorithm=_ALGO)


def decode_token(token: str) -> dict | None:
    """Verify signature + expiry, return payload or None. jwt.verify equivalent."""
    try:
        return jwt.decode(token, _secret(), algorithms=[_ALGO])
    except JWTError:
        return None


# ── register / login business logic ────────────────────────
class AuthError(Exception):
    """Raised for auth failures; the controller maps these to HTTP codes."""
    def __init__(self, status: int, message: str):
        self.status = status
        self.message = message
        super().__init__(message)


def register_user(email: str, password: str, name: str | None) -> dict:
    """Create a user (email must be unique), return {token, user}.

    Live `users` columns: id, email, password (bcrypt hash), created_at.
    `name` is accepted for API compatibility and echoed in the response only.
    """
    sb = get_supabase()
    email = email.lower()

    if sb.table("users").select("id").eq("email", email).execute().data:
        raise AuthError(409, "Email already registered")

    inserted = sb.table("users").insert({
        "email": email,
        "password": hash_password(password),
    }).execute()
    user = inserted.data[0]

    token = create_token(user["id"], email)
    return {"token": token, "user": {"id": user["id"], "email": email, "name": name}}


def login_user(email: str, password: str) -> dict:
    """Verify credentials, return {token, user}."""
    sb = get_supabase()
    email = email.lower()

    res = sb.table("users").select("*").eq("email", email).execute()
    if not res.data:
        raise AuthError(401, "Invalid email or password")

    row = res.data[0]
    stored = row.get("password") or row.get("password_hash") or ""
    if not verify_password(password, stored):
        raise AuthError(401, "Invalid email or password")

    token = create_token(row["id"], email)
    return {"token": token, "user": {"id": row["id"], "email": email, "name": row.get("name")}}
