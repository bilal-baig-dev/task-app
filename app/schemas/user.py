from typing import Annotated

from app.common.validators import validate_password
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserCreate(BaseModel):

    email: EmailStr
    name: str

    password: Annotated[
        str,
        Field(
            min_length=8,
            max_length=128,
            description=(
                "Password must contain at least 8 characters, "
                "one uppercase letter, one lowercase letter, "
                "one digit, and one special character."
            ),
        ),
    ]

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


class UserNotFoundException(Exception):
    pass
