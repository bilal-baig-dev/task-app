import hashlib
from secrets import token_urlsafe

from app.common.constants import PASSWORD_RESET_TOKEN_IN_BYTES
from pwdlib import PasswordHash

password_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(
    password: str,
    password_hash: str,
) -> bool:
    return password_hasher.verify(
        password,
        password_hash,
    )


def hash_token(token: str) -> str:
    return hashlib.sha256(
        token.encode()
    ).hexdigest()


def hash_reset_token(
    token: str,
) -> str:

    return hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()


def generate_password_reset_token() -> str:
    """
    Generate a cryptographically secure
    password reset token.
    """

    return token_urlsafe(PASSWORD_RESET_TOKEN_IN_BYTES)
