from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ClickUpMonthlyList, IntegrationLog
from app.schemas import (
    ClickUpMonthlyListCreate,
    ClickUpMonthlyListResponse,
    IntegrationLogResponse,
)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/clickup-lists", response_model=list[ClickUpMonthlyListResponse])
def list_clickup_lists(db: Session = Depends(get_db)) -> list[ClickUpMonthlyList]:
    return (
        db.query(ClickUpMonthlyList)
        .order_by(ClickUpMonthlyList.year.desc(), ClickUpMonthlyList.month_number.desc())
        .all()
    )


@router.post(
    "/clickup-lists",
    response_model=ClickUpMonthlyListResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_clickup_list(
    payload: ClickUpMonthlyListCreate,
    db: Session = Depends(get_db),
) -> ClickUpMonthlyList:
    existing = (
        db.query(ClickUpMonthlyList)
        .filter(
            ClickUpMonthlyList.year == payload.year,
            ClickUpMonthlyList.month_number == payload.month_number,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ja existe lista cadastrada para esse ano e mes.",
        )

    if payload.active:
        db.query(ClickUpMonthlyList).update({ClickUpMonthlyList.active: False})

    row = ClickUpMonthlyList(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.put("/clickup-lists/{list_db_id}/activate", response_model=ClickUpMonthlyListResponse)
def activate_clickup_list(
    list_db_id: int,
    db: Session = Depends(get_db),
) -> ClickUpMonthlyList:
    row = db.get(ClickUpMonthlyList, list_db_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lista nao encontrada.")

    db.query(ClickUpMonthlyList).update({ClickUpMonthlyList.active: False})
    row.active = True
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("/integration-logs", response_model=list[IntegrationLogResponse])
def list_integration_logs(
    ticket_id: int | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    start_date: datetime | None = Query(default=None),
    end_date: datetime | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db),
) -> list[IntegrationLog]:
    query = db.query(IntegrationLog)

    if ticket_id is not None:
        query = query.filter(IntegrationLog.ticket_id == ticket_id)
    if status_filter:
        query = query.filter(IntegrationLog.status == status_filter)
    if start_date:
        query = query.filter(IntegrationLog.created_at >= start_date)
    if end_date:
        query = query.filter(IntegrationLog.created_at <= end_date)

    return query.order_by(IntegrationLog.created_at.desc()).limit(limit).all()
