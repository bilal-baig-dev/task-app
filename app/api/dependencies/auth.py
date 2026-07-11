from typing import Annotated

from app.db.models import User
from app.db.session import get_db
from app.security.oauth2 import oauth2_scheme
from app.services import auth_service
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession


async def get_current_user(

    token: Annotated[
        str,
        Depends(oauth2_scheme),
    ],

    db: Annotated[
        AsyncSession,
        Depends(get_db),
    ],

) -> User:

    return await auth_service.get_current_user(
        token,
        db,
    )
