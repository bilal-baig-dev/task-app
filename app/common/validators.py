import re


def validate_password(value: str) -> str:
    if not re.search(r"[A-Z]", value):
        raise ValueError(
            "Password must contain at least one uppercase letter.")

    if not re.search(r"[a-z]", value):
        raise ValueError(
            "Password must contain at least one lowercase letter.")

    if not re.search(r"\d", value):
        raise ValueError("Password must contain at least one number.")

    if not re.search(r"[!@#$%^&*()_\-+=\[\]{}|\\:;\"'<>,.?/~`]", value):
        raise ValueError(
            "Password must contain at least one special character.")

    return value
