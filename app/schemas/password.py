from app.common.validators import validate_password
from app.schemas.common import Email, Password
from pydantic import BaseModel, ConfigDict, field_validator, model_validator
from pydantic_core import PydanticCustomError


class ChangePasswordRequest(BaseModel):

    current_password: Password

    new_password: Password

    confirm_password: Password

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, value: str):

        return validate_password(value)

    @model_validator(mode="after")
    def validate_match(self):

        if self.new_password != self.confirm_password:
            raise PydanticCustomError(
                "password_mismatch",
                "Passwords do not match.",
            )

        if self.current_password == self.new_password:
            raise ValueError(
                "New password must be different from current password."
            )

        return self


class ForgotPasswordRequest(BaseModel):

    email: Email

    model_config = ConfigDict(
        extra="forbid"
    )


class ResetPasswordRequest(BaseModel):

    token: str

    new_password: Password

    confirm_password: Password

    model_config = ConfigDict(
        extra="forbid"
    )

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, value: str):

        return validate_password(value)

    @model_validator(mode="after")
    def validate_match(self):

        if self.new_password != self.confirm_password:
            raise ValueError(
                "Passwords do not match."
            )

        return self
