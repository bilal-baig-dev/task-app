import logging
import uuid

from app.common.exceptions import AppException
from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


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


async def unhandled_exception_handler(
    request: Request,
    exc: Exception
):

    trace_id = str(uuid.uuid4())

    logger.exception(
        "Unhandled error trace_id=%s",
        trace_id,
        exc_info=exc
    )

    return JSONResponse(
        status_code=500,
        content={
            "type": "/errors/internal-server-error",
            "title": "Internal Server Error",
            "status": 500,
            "traceId": trace_id,
            "detail": "An unexpected error occurred",
            "instance": str(request.url)
        }
    )
