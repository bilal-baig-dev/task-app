from app.common.responses import ErrorResponse
from app.db.session import get_db
from app.schemas.task import TaskCreate, TaskResponse, TaskUpdate
from app.services import task_service
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"]
)


@router.post(
    "",
    response_model=TaskResponse,
    status_code=201,
    responses={
        500: {
            "model": ErrorResponse,
            "description": "Internal server error"
        }
    })
async def create_task(
    task: TaskCreate,
    db: AsyncSession = Depends(get_db)
):
    return await task_service.create_task(
        db,
        task
    )


@router.get(
    "/{task_id}",
    response_model=TaskResponse
)
async def get_task(
    task_id: str,
    db: AsyncSession = Depends(get_db)
):
    return await task_service.get_task(
        db,
        task_id
    )


@router.put(
    "/{task_id}",
    status_code=204,
    response_model=None
)
async def update_task(
    task_id: str,
    task: TaskUpdate,
    db: AsyncSession = Depends(get_db)
):
    return await task_service.update_task(
        db,
        task_id,
        task
    )
