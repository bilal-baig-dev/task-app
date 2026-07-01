from app.db.session import get_db
from app.schemas.task import TaskResponse
from app.services import task_service
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"]
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
