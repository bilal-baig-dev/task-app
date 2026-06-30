from fastapi import FastAPI

from app.api.routes.user import router
from app.common.exceptions import AppException
from app.core.exception_handlers import app_exception_handler

app = FastAPI(
    title="Task App API",
    description="This is a task app API built with FastAPI and PostgreSQL.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


app.add_exception_handler(
    AppException,
    app_exception_handler
)
app.include_router(router)


@app.get("/health")
async def health():

    return {
        "status": "ok"
    }
