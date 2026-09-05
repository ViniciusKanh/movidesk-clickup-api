from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ClickUpMonthlyList(Base):
    __tablename__ = "clickup_monthly_lists"
    __table_args__ = (
        UniqueConstraint("year", "month_number", name="uq_clickup_monthly_list_year_month"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    month_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    month_name: Mapped[str] = mapped_column(String(30), nullable=False)
    clickup_folder_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    clickup_folder_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    clickup_list_name: Mapped[str] = mapped_column(String(120), nullable=False)
    clickup_list_id: Mapped[str] = mapped_column(String(80), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)


class IntegrationLog(Base):
    __tablename__ = "integration_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ticket_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    ticket_subject: Mapped[str | None] = mapped_column(String(500), nullable=True)
    movidesk_payload: Mapped[str | None] = mapped_column(Text, nullable=True)
    clickup_task_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    clickup_task_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
