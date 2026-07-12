from typing import Annotated

from app.api.dependencies.auth import get_current_user
from app.db.models import User
from app.db.session import get_db
from app.schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
)
from app.schemas.user import UserResponse
from app.services import auth_service
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=201,
)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):

    return await auth_service.register(
        db,
        request,
    )


@router.post(
    "/login",
    response_model=TokenResponse,
)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
):

    return await auth_service.login(
        db,
        request,
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
)
async def refresh_token(
    request: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):

    return await auth_service.refresh(
        db,
        request,
    )


@router.post(
    "/logout",
    status_code=204,
)
async def logout(
    request: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):

    await auth_service.logout(
        db,
        request.refresh_token,
    )


@router.get(
    "/me",
    response_model=UserResponse,
)
async def me(
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],

):

    return current_user


@router.post(
    "/change-password",
    status_code=204,
)
async def change_password(
    request: ChangePasswordRequest,
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    db: Annotated[
        AsyncSession,
        Depends(get_db),
    ],

):

    await auth_service.change_password(
        db,
        current_user,
        request,
    )


@router.post(
    "/forgot-password",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def forgot_password(
    request: ForgotPasswordRequest,
    db: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
):

    await auth_service.forgot_password(
        db,
        request.email,
    )


@router.post(
    "/reset-password",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def reset_password(
    request: ResetPasswordRequest,
    db: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
):

    await auth_service.reset_password(
        db,
        request,
    )
