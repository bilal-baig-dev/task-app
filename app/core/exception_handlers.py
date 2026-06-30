from app.common.exceptions import AppException
from fastapi import Request
from fastapi.responses import JSONResponse


async def app_exception_handler(
    request: Request,
    exc: AppException
):

    return JSONResponse(
        status_code=exc.status,
        content={
            "type": exc.type,
            "title": exc.title,
            "status": exc.status,
            "traceId": exc.traceId,
            "detail": exc.detail,
            "instance": str(request.url)
        }
    )
