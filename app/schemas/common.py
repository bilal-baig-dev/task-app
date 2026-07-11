from typing import Annotated, Generic, List, TypeVar

from pydantic import BaseModel, EmailStr, Field, StringConstraints

# Create a TypeVar that represents any Pydantic model
T = TypeVar("T", bound=BaseModel)


# Define the standard envelope wrapper
class PaginatedResponse(BaseModel, Generic[T]):
    count: int
    data: List[T]


Email = Annotated[
    EmailStr,
    Field(
        description="User email address",
        examples=["john@example.com"],
    ),
]

UUID = Annotated[
    str,
    Field(
        min_length=36,
        max_length=36,
    ),
]

Name = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=2,
        max_length=255,
    ),
]

Password = Annotated[
    str,
    StringConstraints(
        min_length=8,
        max_length=128,
        description=(
            "Password must contain at least 8 characters, "
            "one uppercase letter, one lowercase letter, "
            "one digit, and one special character."
        ),
    ),
]
