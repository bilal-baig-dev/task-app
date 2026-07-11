from app.common.validators import validate_password
from app.schemas.common import Email, Name, Password
from pydantic import BaseModel, ConfigDict, field_validator, model_validator


class RegisterRequest(BaseModel):

    email: Email

    name: Name

    password: Password

    confirm_password: Password

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    @field_validator("password")
    @classmethod
    def validate_password(
        cls,
        value: str,
    ) -> str:
        return validate_password(value)

    @model_validator(mode="after")
    def validate_passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError(
                "Passwords do not match."
            )

        return self


class LoginRequest(BaseModel):

    email: Email

    password: Password

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )


class RegisterResponse(BaseModel):

    message: str


class ResendVerificationEmailRequest(BaseModel):

    email: Email

    model_config = ConfigDict(
        extra="forbid"
    )


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int


class RefreshRequest(BaseModel):

    refresh_token: str
