from enum import IntEnum


class StatusSeverity(IntEnum):
    NONE = 0
    NORMAL = 1
    HIGH = 2
    ONHOLD = 3


class TaskStatus(IntEnum):
    NOT_STARTED = 1
    IN_PROGRESS = 2
    COMPLETED = 3
