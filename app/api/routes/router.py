from app.api.routes import auth, task, user
from fastapi import APIRouter

api_router = APIRouter(
    prefix="/api/v1"
)


api_router.include_router(user.router)
api_router.include_router(task.router)
api_router.include_router(auth.router)
