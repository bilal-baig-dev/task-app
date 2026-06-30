from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ListResponse(BaseModel, Generic[T]):
    count: int
    data: list[T]


class ErrorResponse(BaseModel):
    type: str
    title: str
    status: int
    traceId: str
    detail: str
    instance: str
