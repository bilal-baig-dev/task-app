from functools import lru_cache

from app.common.constants import PASSWORD_RESET_TOKEN_EXPIRE_MINUTES
from pydantic import AnyHttpUrl, EmailStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    APP_NAME: str = "My API"
    DEBUG: bool = False

    DATABASE_URL: str

    SECRET_KEY: str

    JWT_ALGORITHM: str

    ACCESS_TOKEN_EXPIRE_MINUTES: int

    REFRESH_TOKEN_EXPIRE_DAYS: int

    MAILGUN_API_KEY: str

    MAILGUN_DOMAIN: str

    MAIL_FROM: EmailStr

    FRONTEND_URL: AnyHttpUrl

    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = PASSWORD_RESET_TOKEN_EXPIRE_MINUTES

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True
    )


@lru_cache
def get_settings():
    return Settings()


settings = get_settings()
