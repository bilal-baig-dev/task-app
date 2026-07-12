import uuid


class AppException(Exception):

    def __init__(
        self,
        *,
        type: str,
        title: str,
        status: int,
        detail: str,
        instance: str = ""
    ):

        self.type = type
        self.title = title
        self.status = status
        self.detail = detail
        self.instance = instance
        self.traceId = str(uuid.uuid4())

        super().__init__(detail)


class NotFoundException(AppException):

    def __init__(self, detail: str):

        super().__init__(
            type="/errors/not-found",
            title="Resource not found",
            status=404,
            detail=detail
        )


class ConflictException(AppException):

    def __init__(self, detail: str):

        super().__init__(
            type="/errors/conflict",
            title="Conflict",
            status=409,
            detail=detail
        )


class UnauthorizedException(AppException):

    def __init__(self, detail="Unauthorized"):

        super().__init__(
            type="/errors/unauthorized",
            title="Unauthorized",
            status=401,
            detail=detail
        )


class ForbiddenException(AppException):

    def __init__(self, detail="Forbidden"):

        super().__init__(
            type="/errors/forbidden",
            title="Forbidden",
            status=403,
            detail=detail
        )


class DatabaseException(AppException):

    def __init__(
        self,
        detail="Database operation failed"
    ):
        super().__init__(
            type="/errors/database",
            title="Database Error",
            status=500,
            detail=detail
        )


class InvalidTokenException(
    UnauthorizedException
):

    def __init__(self, detail: str):

        super().__init__(detail)


class ValidationException(AppException):

    def __init__(self, detail: str):

        super().__init__(
            type="/errors/validation",
            title="Validation Error",
            status=422,
            detail=detail
        )
