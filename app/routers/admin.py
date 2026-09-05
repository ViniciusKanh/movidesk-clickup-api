from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ClickUpMonthlyList, IntegrationLog
from app.schemas import (
    AdminLoginRequest,
    AdminLoginResponse,
    ClickUpFolderListItem,
    ClickUpFolderSetupRequest,
    ClickUpMonthlyListCreate,
    ClickUpMonthlyListResponse,
    IntegrationLogResponse,
)
from app.services.clickup_service import ClickUpService, ClickUpServiceError
from app.utils.admin_auth import (
    clear_session_cookie,
    create_session_cookie,
    require_admin_session,
    verify_admin_credentials,
)

router = APIRouter(prefix="/admin", tags=["admin"])

MESES_PT_BR = {
    1: "Janeiro",
    2: "Fevereiro",
    3: "Marco",
    4: "Abril",
    5: "Maio",
    6: "Junho",
    7: "Julho",
    8: "Agosto",
    9: "Setembro",
    10: "Outubro",
    11: "Novembro",
    12: "Dezembro",
}


# ---------------------------------------------------------------------------
# Autenticacao do painel (login/logout por sessao)
# ---------------------------------------------------------------------------


@router.post("/login", response_model=AdminLoginResponse)
def login(payload: AdminLoginRequest, response: Response) -> AdminLoginResponse:
    if not verify_admin_credentials(payload.username, payload.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario ou senha invalidos.")

    create_session_cookie(response, payload.username)
    return AdminLoginResponse(success=True)


@router.post("/logout", response_model=AdminLoginResponse)
def logout(response: Response) -> AdminLoginResponse:
    clear_session_cookie(response)
    return AdminLoginResponse(success=True)


@router.get("/me")
def me(username: str = Depends(require_admin_session)) -> dict[str, str]:
    return {"username": username}


# ---------------------------------------------------------------------------
# ClickUp: resolucao de pasta (Folder) -> listas
# ---------------------------------------------------------------------------


@router.get("/clickup/folders/{folder_id}/lists", response_model=list[ClickUpFolderListItem])
async def get_folder_lists(
    folder_id: str,
    _: str = Depends(require_admin_session),
) -> list[ClickUpFolderListItem]:
    clickup = ClickUpService()
    try:
        lists = await clickup.get_folder_lists(folder_id)
    except ClickUpServiceError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    if not lists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nenhuma lista encontrada nessa pasta (verifique o Folder ID e o token do ClickUp).",
        )

    return [ClickUpFolderListItem(**item) for item in lists]


@router.post(
    "/clickup/folders/setup",
    response_model=ClickUpMonthlyListResponse,
    status_code=status.HTTP_201_CREATED,
)
def setup_clickup_folder(
    payload: ClickUpFolderSetupRequest,
    db: Session = Depends(get_db),
    _: str = Depends(require_admin_session),
) -> ClickUpMonthlyList:
    """Fluxo simplificado do painel: escolher pasta + lista do mes atual e ja ativar.

    Preenche automaticamente ano/mes a partir da data atual do servidor. Se ja existir
    um cadastro para o mes/ano atual, atualiza-o em vez de duplicar.
    """
    now = datetime.now(timezone.utc)

    existing = (
        db.query(ClickUpMonthlyList)
        .filter(
            ClickUpMonthlyList.year == now.year,
            ClickUpMonthlyList.month_number == now.month,
        )
        .first()
    )

    db.query(ClickUpMonthlyList).update({ClickUpMonthlyList.active: False})

    if existing:
        existing.clickup_folder_id = payload.clickup_folder_id
        existing.clickup_folder_name = payload.clickup_folder_name
        existing.clickup_list_id = payload.clickup_list_id
        existing.clickup_list_name = payload.clickup_list_name
        existing.active = True
        db.add(existing)
        db.commit()
        db.refresh(existing)
        return existing

    row = ClickUpMonthlyList(
        year=now.year,
        month_number=now.month,
        month_name=MESES_PT_BR[now.month],
        clickup_folder_id=payload.clickup_folder_id,
        clickup_folder_name=payload.clickup_folder_name,
        clickup_list_id=payload.clickup_list_id,
        clickup_list_name=payload.clickup_list_name,
        active=True,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


# ---------------------------------------------------------------------------
# Listas mensais do ClickUp (cadastro manual / historico)
# ---------------------------------------------------------------------------


@router.get("/clickup-lists", response_model=list[ClickUpMonthlyListResponse])
def list_clickup_lists(
    db: Session = Depends(get_db),
    _: str = Depends(require_admin_session),
) -> list[ClickUpMonthlyList]:
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
    _: str = Depends(require_admin_session),
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
    _: str = Depends(require_admin_session),
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


# ---------------------------------------------------------------------------
# Logs de integracao
# ---------------------------------------------------------------------------


@router.get("/integration-logs", response_model=list[IntegrationLogResponse])
def list_integration_logs(
    ticket_id: int | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    start_date: datetime | None = Query(default=None),
    end_date: datetime | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db),
    _: str = Depends(require_admin_session),
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
