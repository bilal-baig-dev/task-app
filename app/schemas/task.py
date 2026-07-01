from app.common.enums import StatusSeverity, TaskStatus
from app.schemas.user import UserResponse
from pydantic import BaseModel


class TaskCreate(BaseModel):
    name: str
    description: str | None = None
    group: str | None = None
    priority: StatusSeverity = StatusSeverity.NONE
    status: TaskStatus = TaskStatus.NOT_STARTED
    start_time: str | None = None
    due_time: str | None = None
    user_id: str


class TaskResponse(BaseModel):

    id: str
    name: str
    description: str | None = None
    group: str | None = None
    priority: StatusSeverity = StatusSeverity.NONE
    status: TaskStatus = TaskStatus.NOT_STARTED
    start_time: str | None = None
    due_time: str | None = None
    user: UserResponse | None = None

    model_config = {
        "from_attributes": True
    }
