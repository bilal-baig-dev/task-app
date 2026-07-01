from app.common.exceptions import ConflictException, DatabaseException
from app.db.models.task import Task
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


async def get_task(
    db: AsyncSession,
    task_id: str
):

    result = await db.execute(
        select(Task).
        options(selectinload(Task.user)).
        where(Task.id == task_id)
    )

    return result.scalar_one_or_none()


async def create_task(
        db: AsyncSession,
        task: Task
):

    try:
        task = Task(
            **task.model_dump(),
            user_id=task.user_id
        )
        db.add(task)
        await db.commit()
        await db.refresh(task)
        return task
    except IntegrityError as exc:
        await db.rollback()
        raise ConflictException("Task could not be created") from exc
    except SQLAlchemyError as exc:
        await db.rollback()
        raise DatabaseException() from exc
