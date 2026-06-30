from app.common.exceptions import NotFoundException
from app.db.models.user import User
from app.schemas.user import UserCreate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def create_user(
    db: AsyncSession,
    data: UserCreate
):

    user = User(
        email=data.email,
        name=data.name
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
