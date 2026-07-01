from app.common.responses import ErrorResponse
from app.db.session import get_db
from app.schemas.user import EmailQueryParam, UserCreate, UserResponse, UserUpdate
from app.services import user_service
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(
    prefix="/users",
    tags=["users"]
)


@router.post(
    "",
    response_model=UserResponse,
    status_code=201,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not found"
        },
        500: {
            "model": ErrorResponse,
            "description": "Internal server error"
        }
    }
)
async def create(
    data: UserCreate,
    db: AsyncSession = Depends(get_db)
):

    return await user_service.create_user(db, data)


@router.get(
    "",
    response_model=list[UserResponse]
)
async def list_users(
    db: AsyncSession = Depends(get_db)
):

    return await user_service.get_users(db)


@router.get(
    "/find-by-email",
    response_model=UserResponse
)
async def get_user_by_email(
    query: EmailQueryParam = Depends(),
    db: AsyncSession = Depends(get_db)
):

    return await user_service.find_user_by_email(db, query.email)


@router.put(
    "/{user_id}",
    status_code=204,
    response_model=None
)
async def update_user(
    user_id: str,
    user: UserUpdate,
    db: AsyncSession = Depends(get_db)
):
    return await user_service.update_user(
        db,
        user_id,
        user
    )
