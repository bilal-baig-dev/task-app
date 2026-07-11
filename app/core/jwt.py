import uuid
from datetime import UTC, datetime, timedelta
from secrets import token_urlsafe

import jwt
from app.common.constants import BYTES_COUNT
from app.common.exceptions import InvalidTokenException
from app.core.config import settings


def _create_token(
    *,
    user_id: str,
    expires_delta: timedelta,
    token_type: str,
) -> str:

    now = datetime.now(UTC)

    payload = {
        "sub": user_id,
        "jti": str(uuid.uuid4()),
        "type": token_type,
        "iat": now,
        "nbf": now,
        "exp": now + expires_delta,
    }

    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def create_access_token(
    user_id: str,
) -> str:

    return _create_token(
        user_id=user_id,
        expires_delta=timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        ),
        token_type="access",
    )


def create_refresh_token() -> str:

    return token_urlsafe(BYTES_COUNT)


def decode_token(
    token: str,
) -> dict:

    return jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )


def verify_token(token: str) -> dict:

    try:
        return decode_token(token)

    except jwt.ExpiredSignatureError:
        raise InvalidTokenException(
            "Token has expired"
        )

    except jwt.InvalidTokenError:
        raise InvalidTokenException(
            "Invalid token"
        )


def decode_access_token(
    token: str,
) -> dict:

    return jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )
