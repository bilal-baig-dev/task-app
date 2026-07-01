from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from app.common.enums import StatusSeverity, TaskStatus
from app.db.base import Base
from sqlalchemy import DateTime, Enum, ForeignKey, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.db.models.user import User


class Task(Base):

    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    name: Mapped[str] = mapped_column(
        String(255),
    )

    description: Mapped[str] = mapped_column(
        String(500),
        nullable=True
    )

    group: Mapped[str] = mapped_column(
        String(255),
        nullable=True
    )

    priority: Mapped[StatusSeverity] = mapped_column(
        Enum(StatusSeverity),
        default=StatusSeverity.NONE,
        nullable=False
    )

    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus),
        default=TaskStatus.NOT_STARTED,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP")
    )

    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True)

    due_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True)

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="tasks")
