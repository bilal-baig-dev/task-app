
from datetime import datetime

from app.common.validators import validate_password
from app.schemas.common import Email, Name, Password
from pydantic import BaseModel, ConfigDict, EmailStr, field_validator


class UserCreate(BaseModel):

    email: Email
    name: Name

    password: Password

    model_config = ConfigDict(extra="forbid")

    @field_validator("password")
    @classmethod
    def password_validator(cls, value: str) -> str:
        return validate_password(value)


class UserUpdate(BaseModel):
    name: str


class UserResponse(BaseModel):

    id: str
    email: EmailStr
    name: str

    model_config = {
        "from_attributes": True
    }


class EmailQueryParam(BaseModel):
    email: EmailStr

    from datetime import datetime


class CurrentUserResponse(BaseModel):

    id: str

    email: EmailStr

    name: str

    is_verified: bool

    is_active: bool

    last_login_at: datetime | None

    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )


class MeResponse(CurrentUserResponse):
    pass
