from app.db.models.task import Task
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


async def get_task(
    db: AsyncSession,
    task_id: str
):

    result = await db.execute(
        select(Task)
        .options(
            selectinload(Task.user)
        )
        .where(Task.id == task_id)
    )

    return result.scalar_one_or_none()
