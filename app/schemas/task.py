
from app.common.enums import StatusSeverity, TaskStatus
from app.schemas.user import UserResponse
from pydantic import BaseModel, ConfigDict


class TaskBase(BaseModel):
    name: str
    description: str | None = None
    group: str | None = None
    priority: StatusSeverity = StatusSeverity.NONE
    status: TaskStatus = TaskStatus.NOT_STARTED
    start_time: str | None = None
    due_time: str | None = None


class TaskCreate(TaskBase):
    model_config = ConfigDict(extra="forbid")
    user_id: str


class TaskUpdate(TaskBase):
    name: str | None = None
    description: str | None = None
    group: str | None = None
    priority: StatusSeverity | None = None
    status: TaskStatus | None = None
    start_time: str | None = None
    due_time: str | None = None
    model_config = ConfigDict(extra="forbid")


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
