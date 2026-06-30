from app.common.responses import ErrorResponse
from app.db.session import get_db
from app.schemas.user import EmailQueryParam, UserCreate, UserResponse
from app.services.user_service import create_user, find_user_by_email, get_users
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

    return await create_user(db, data)


@router.get(
    "",
    response_model=list[UserResponse]
)
async def list_users(
    db: AsyncSession = Depends(get_db)
):

    return await get_users(db)


@router.get(
    "/find-by-email",
    response_model=UserResponse
)
async def get_user_by_email(
    query: EmailQueryParam = Depends(),
    db: AsyncSession = Depends(get_db)
):

    return await find_user_by_email(db, query.email)
