from app.common.exceptions import (
    ConflictException,
    DatabaseException,
    NotFoundException,
)
from app.core.security import hash_password
from app.db.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession


async def create_user(
    db: AsyncSession,
    data: UserCreate
):

    user = User(
        email=data.email,
        name=data.name,
        password_hash=hash_password(data.password),
    )

    db.add(user)

    await db.commit()
    await db.refresh(user)

    return user


async def get_users(
    db: AsyncSession
):

    result = await db.execute(
        select(User)
    )

    return result.scalars().all()


async def find_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(
        select(User).where(User.email == email)
    )

    user = result.scalars().first()

    if user is None:
        raise NotFoundException(
            "User with email does not exist"
        )

    return user


async def update_user(
    db: AsyncSession,
    user_id: str,
    user: UserUpdate
):
    try:
        await db.execute(update(User).where(User.id == user_id).values(
            **user.model_dump(
                exclude_unset=True
            )
        ))
        await db.commit()
        return None
    except IntegrityError as exc:
        await db.rollback()
        raise ConflictException("User could not be updated") from exc
    except SQLAlchemyError as exc:
        await db.rollback()
        raise DatabaseException() from exc
