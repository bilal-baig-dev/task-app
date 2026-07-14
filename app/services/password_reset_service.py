from datetime import UTC, datetime

from app.db.models.password_reset_token import PasswordResetToken
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession


async def create(
    db: AsyncSession,
    token: PasswordResetToken,
) -> PasswordResetToken:

    db.add(token)

    await db.flush()

    return token


async def get_by_hash(
    db: AsyncSession,
    token_hash: str,
) -> PasswordResetToken | None:

    result = await db.execute(
        select(PasswordResetToken)
        .where(
            PasswordResetToken.token_hash == token_hash,
        )
    )

    return result.scalar_one_or_none()


async def mark_used(
    db: AsyncSession,
    token_id: str,
) -> None:

    await db.execute(
        update(PasswordResetToken)
        .where(
            PasswordResetToken.id == token_id,
        )
        .values(
            used=True,
        )
    )


async def delete_user_tokens(
    db: AsyncSession,
    user_id: str,
) -> None:

    await db.execute(
        delete(PasswordResetToken)
        .where(
            PasswordResetToken.user_id == user_id,
        )
    )


async def delete_expired(
    db: AsyncSession,
) -> None:

    await db.execute(
        delete(PasswordResetToken)
        .where(
            PasswordResetToken.expires_at
            < datetime.now(UTC)
        )
    )


async def get_valid_token(
    db: AsyncSession,
    token_hash: str,
) -> PasswordResetToken | None:

    result = await db.execute(
        select(PasswordResetToken)
        .where(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.used.is_(False),
            PasswordResetToken.expires_at > datetime.now(UTC)
        )
    )

    return result.scalar_one_or_none()
