"""Auth ROUTER — maps URLs to controller handlers.

Login/register are public (IP rate-limited).
/me is protected with JWT.
"""
from fastapi import APIRouter, Depends

from controllers.auth_controller import login, me, register
from middleware.auth_middleware import get_current_user
from middleware.rate_limiter_middleware import AuthLimit

router = APIRouter(prefix="/auth", tags=["auth"])

router.post("/register", dependencies=[Depends(AuthLimit)])(register)
router.post("/login", dependencies=[Depends(AuthLimit)])(login)
router.get("/me", dependencies=[Depends(get_current_user)])(me)
