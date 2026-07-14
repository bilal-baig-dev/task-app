
from datetime import UTC, datetime

from app.db.models import RefreshToken
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession


async def create_refresh_token(
    db: AsyncSession,
    refresh_token: RefreshToken,
):
    db.add(refresh_token)

    await db.commit()

    await db.refresh(refresh_token)

    return refresh_token


async def get_refresh_token(
    db: AsyncSession,
    token_hash: str,
):
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash
        )
    )

    return result.scalar_one_or_none()


async def revoke(
    db: AsyncSession,
    refresh_token: RefreshToken,
) -> None:

    refresh_token.revoked = True

    await db.commit()


async def delete_expired(
    db: AsyncSession,
) -> None:

    await db.execute(
        delete(RefreshToken).where(
            RefreshToken.expires_at < datetime.now(UTC)
        )
    )

    await db.commit()


async def delete_all_by_user(
    db: AsyncSession,
    user_id: str,
) -> None:

    await db.execute(
        delete(RefreshToken).where(
            RefreshToken.user_id == user_id
        )
    )
