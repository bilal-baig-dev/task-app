from app.common.exceptions import (
    ConflictException,
    DatabaseException,
    NotFoundException,
)
from app.common.query import ListParams, list_records
from app.db.models import Task, User
from app.schemas.common import PaginatedResponse
from app.schemas.task import TaskCreate, TaskResponse, TaskUpdate
from sqlalchemy import delete, select, update
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
        task: TaskCreate
):

    try:
        new_task = Task(
            **task.model_dump()
        )

        db.add(new_task)
        await db.commit()
        await db.refresh(new_task,  attribute_names=['user'])
        return new_task
    except IntegrityError as exc:
        await db.rollback()
        raise ConflictException("Task could not be created") from exc
    except SQLAlchemyError as exc:
        await db.rollback()
        raise DatabaseException() from exc


async def update_task(
        db: AsyncSession,
        task_id: str,
        task: TaskUpdate
):
    try:
        await db.execute(update(Task).where(Task.id == task_id).values(
            **task.model_dump(
                exclude_unset=True
            )
        ))
        await db.commit()
        return None
    except IntegrityError as exc:
        await db.rollback()
        raise ConflictException("Task could not be updated") from exc
    except SQLAlchemyError as exc:
        await db.rollback()
        raise DatabaseException() from exc


async def delete_task(
    db: AsyncSession,
    task_id: str,
) -> None:

    try:
        result = await db.execute(
            delete(Task)
            .where(Task.id == task_id)
            .returning(Task.id)
        )

        deleted_task_id = result.scalar_one_or_none()
        if deleted_task_id is None:
            raise NotFoundException(
                "Task not exists"
            )

        await db.commit()
        return None

    except IntegrityError as exc:
        await db.rollback()
        raise ConflictException(
            "Task cannot be deleted"
        ) from exc

    except SQLAlchemyError as exc:
        await db.rollback()
        raise DatabaseException() from exc


async def list_tasks(
    db: AsyncSession,
    current_user: User,
    params: ListParams
) -> PaginatedResponse[TaskResponse]:
    return await list_records(db, Task, TaskResponse, params,
                              extra_conditions=[Task.user_id == current_user.id])
