
from datetime import UTC, datetime, timedelta

from app.common.constants import MINTUE_TO_SECONDS
from app.common.exceptions import (
    ConflictException,
    DatabaseException,
    UnauthorizedException,
    ValidationException,
)
from app.core.config import settings
from app.core.jwt import create_access_token, create_refresh_token, decode_access_token
from app.core.security import (
    generate_password_reset_token,
    hash_password,
    hash_reset_token,
    verify_password,
)
from app.core.security import hash_token as hash_refresh_token
from app.db.models import PasswordResetToken, RefreshToken, User
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
)
from app.services import email_service as EmailService
from app.services import password_reset_service, refresh_token_service, user_service
from jose import JWTError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession


async def register(
    db: AsyncSession,
    request: RegisterRequest,
) -> User:

    existing = await user_service.find_user_by_email(
        db,
        request.email,
    )

    if existing:
        raise ConflictException(
            "Email already exists."
        )

    user = User(
        email=request.email,
        name=request.name,
        password_hash=hash_password(
            request.password
        ),
    )

    db.add(user)

    await db.commit()
    await db.refresh(user)

    return user


async def login(
    db: AsyncSession,
    request: LoginRequest,
) -> TokenResponse:

    user = await user_service.find_user_by_email(
        db,
        request.email,
    )

    if user is None:
        raise UnauthorizedException(
            "Invalid email or password."
        )

    if not verify_password(
        request.password,
        user.password_hash,
    ):
        raise UnauthorizedException(
            "Invalid email or password."
        )

    # Generate access token JWT and refresh token
    access_token = create_access_token(
        user.id
    )

    refresh_token = create_refresh_token()

    hashed_token = hash_refresh_token(
        refresh_token,
    )

    expires_at = datetime.now(UTC) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS,
    )

    # Create a new RefreshToken instance and add it to the database
    refresh_token_db_object = RefreshToken(
        token_hash=hashed_token,
        user_id=user.id,
        expires_at=expires_at
    )

    db.add(refresh_token_db_object)

    await db.commit()
    await db.refresh(refresh_token_db_object)

    # Return the access token and refresh token in the response
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * MINTUE_TO_SECONDS
    )


async def refresh(
    db: AsyncSession,
    request: RefreshRequest,
) -> TokenResponse:

    hashed = hash_refresh_token(
        request.refresh_token,
    )

    session = await refresh_token_service.get_refresh_token(
        db,
        hashed,
    )

    if session is None:
        raise UnauthorizedException(
            "Invalid refresh token."
        )

    if session.revoked:
        raise UnauthorizedException(
            "Refresh token revoked."
        )

    if session.expires_at < datetime.now(UTC):
        raise UnauthorizedException(
            "Refresh token expired."
        )

    await refresh_token_service.revoke(
        db,
        session,
    )

    new_refresh = create_refresh_token()

    hashed_new = hash_refresh_token(
        new_refresh,
    )

    expires_at = datetime.now(UTC) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS,
    )

 # Create a new RefreshToken instance and add it to the database
    refresh_token = RefreshToken(
        token_hash=hashed_new,
        user_id=session.user_id,
        expires_at=expires_at
    ),

    db.add(refresh_token)

    await db.commit()
    await db.refresh(refresh_token)

    access = create_access_token(
        subject=session.user_id,
    )

    return TokenResponse(
        access_token=access,
        refresh_token=new_refresh,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * MINTUE_TO_SECONDS
    )


async def logout(
    db: AsyncSession,
    refresh_token: str,
) -> None:

    hashed = hash_refresh_token(
        refresh_token
    )

    token = await refresh_token_service.get_refresh_token(
        db,
        hashed
    )

    if token is None:
        return

    await refresh_token_service.revoke(
        db,
        token
    )


async def get_current_user(
    token: str,
    db: AsyncSession,
) -> User:

    try:

        payload = decode_access_token(
            token
        )

    except JWTError as exc:
        raise UnauthorizedException(
            "Invalid access token."
        ) from exc

    user_id = payload.get("sub")

    if user_id is None:
        raise UnauthorizedException(
            "Invalid access token."
        )

    user = await user_service.get_user_by_id(
        db,
        user_id,
    )

    if user is None:
        raise UnauthorizedException(
            "User not found."
        )

    return user


async def change_password(
    db: AsyncSession,
    current_user: User,
    request: ChangePasswordRequest,
) -> None:

    if not verify_password(
        request.current_password,
        current_user.password_hash
    ):

        raise UnauthorizedException(
            "Current password is incorrect."
        )

    if verify_password(
        request.new_password,
        current_user.password_hash,
    ):

        raise ValidationException(
            "New password must be different."
        )

    current_user.password_hash = hash_password(
        request.new_password
    )

    await db.commit()


async def forgot_password(
    db: AsyncSession,
    email: str,
) -> None:

    user = await user_service.find_user_by_email(
        db,
        email,
    )

    #
    # IMPORTANT
    #
    # Never reveal whether an account exists.
    #
    if user is None:
        return

    raw_token = generate_password_reset_token()

    token = PasswordResetToken(
        token_hash=hash_reset_token(raw_token),
        expires_at=datetime.now(UTC)
        + timedelta(
            minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES
        ),
        user_id=user.id
    )

    await password_reset_service.create(
        db,
        token,
    )

    await db.commit()

    reset_link = (
        f"{settings.FRONTEND_URL}"
        f"/reset-password"
        f"?token={raw_token}"
    )

    await EmailService.send_password_reset_email(
        email=user.email,
        reset_link=reset_link
    )


async def reset_password(
    db: AsyncSession,
    request: ResetPasswordRequest,
) -> None:
    try:
        token = await password_reset_service.get_valid_token(
            db,
            hash_reset_token(
                request.token
            ),
        )

        if token is None:

            raise UnauthorizedException(
                "Invalid or expired password reset token."
            )

        user = token.user

        if verify_password(
            request.new_password,
            user.password_hash
        ):

            raise ValidationException(
                "New password must be different from the current password."
            )

        user.password_hash = hash_password(
            request.new_password
        )

        await refresh_token_service.delete_all_by_user(
            db,
            user.id
        )

        await password_reset_service.delete_user_tokens(
            db,
            user.id
        )

        await db.commit()

    except SQLAlchemyError as exc:

        await db.rollback()

        raise DatabaseException() from exc
