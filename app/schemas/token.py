from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field


class AccessToken(BaseModel):

    access_token: str = Field(
        description="JWT access token"
    )

    expires_in: int = Field(
        description="Access token expiration in seconds"
    )

    model_config = ConfigDict(
        extra="forbid"
    )


class RefreshToken(BaseModel):

    refresh_token: str = Field(
        description="JWT refresh token"
    )

    refresh_expires_in: int = Field(
        description="Refresh token expiration in seconds"
    )

    model_config = ConfigDict(
        extra="forbid"
    )


class TokenPair(BaseModel):

    access_token: str

    refresh_token: str

    token_type: Literal["Bearer"] = "Bearer"

    expires_in: int

    refresh_expires_in: int

    expires_at: datetime

    refresh_expires_at: datetime

    model_config = ConfigDict(
        extra="forbid"
    )

    @computed_field
    @property
    def authorization_header(self) -> str:
        return f"Bearer {self.access_token}"

    from pydantic import BaseModel


class RefreshTokenRequest(BaseModel):

    refresh_token: str

    model_config = ConfigDict(
        extra="forbid"
    )

    from pydantic import BaseModel


class LogoutRequest(BaseModel):

    refresh_token: str

    logout_all_devices: bool = False

    model_config = ConfigDict(
        extra="forbid"
    )

    from pydantic import BaseModel


class VerifyEmailRequest(BaseModel):

    token: str

    model_config = ConfigDict(
        extra="forbid"
    )

    from datetime import datetime


class TokenPayload(BaseModel):

    sub: str

    jti: str

    type: str

    iat: datetime

    exp: datetime

    nbf: datetime

    model_config = ConfigDict(
        extra="ignore"
    )


class ValidateTokenResponse(BaseModel):

    valid: bool

    payload: TokenPayload | None = None
