"""Auth MIDDLEWARE — the Python equivalent of your Node `verifyToken`.

In Express you'd write:
    const verifyToken = (req, res, next) => {
        const token = req.headers.authorization?.split(' ')[1];
        const decoded = jwt.verify(token, secret);
        req.user = decoded; next();
    }

In FastAPI the same job is done by a dependency: any route that adds
`user = Depends(get_current_user)` becomes protected, and `user` holds the
decoded identity — just like `req.user` after your middleware runs.
"""
from fastapi import Header, HTTPException

from services.auth_service import decode_token


def get_current_user(authorization: str = Header(default="")) -> dict:
    """Read `Authorization: Bearer <jwt>`, verify it, return {id, email}.
    Raises 401 if the token is missing, malformed, invalid, or expired."""
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")

    token = authorization.split(" ", 1)[1].strip()
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return {"id": payload["sub"], "email": payload.get("email", "")}
