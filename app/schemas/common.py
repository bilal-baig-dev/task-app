from typing import Generic, List, TypeVar

from pydantic import BaseModel

# Create a TypeVar that represents any Pydantic model
T = TypeVar("T", bound=BaseModel)


# Define the standard envelope wrapper
class PaginatedResponse(BaseModel, Generic[T]):
    count: int
    data: List[T]
