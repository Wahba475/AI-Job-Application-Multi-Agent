"""Auth ROUTER — maps URLs to controller handlers (same role as your Node
Routers/ files: router.post('/register', register)).
"""
from fastapi import APIRouter
from controllers.auth_controller import register, login, me

router = APIRouter(prefix="/auth", tags=["auth"])

router.post("/register")(register)   # POST /api/auth/register
router.post("/login")(login)         # POST /api/auth/login
router.get("/me")(me)                # GET  /api/auth/me   (protected)
