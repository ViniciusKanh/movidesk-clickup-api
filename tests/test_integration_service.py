import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.models import Base, IntegrationLog
from app.schemas import MovideskTicket
from app.services.integration_service import IntegrationService, STATUS_CREATED, STATUS_ERROR_VALIDATION
from app.services.movidesk_service import MovideskService
from app.services.clickup_service import ClickUpService


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    testing_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = testing_session()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def make_valid_ticket(**overrides):
    data = {
        "raw": {},
        "id": 717525,
        "subject": "Melhoria no Dashboard",
        "status": "Novo",
        "service_first_level": "GSI",
        "service_second_level": "BI",
        "service_third_level": "Melhoria/Projeto",
        "custom_fields": {"[BI] Criar tarefa no ClickUp?": "Sim", "[BI] Link ClickUp": ""},
    }
    data.update(overrides)
    return MovideskTicket(**data)


def test_extract_ticket_id_variations():
    assert IntegrationService.extract_ticket_id({"Id": 717525}) == 717525
    assert IntegrationService.extract_ticket_id({"id": "717525"}) == 717525
    assert IntegrationService.extract_ticket_id({"TicketId": 717525}) == 717525
    assert IntegrationService.extract_ticket_id({"ticketId": 717525}) == 717525
    assert IntegrationService.extract_ticket_id({"ticket_id": 717525}) == 717525
    assert IntegrationService.extract_ticket_id({"Ticket.Id": 717525}) == 717525
    assert IntegrationService.extract_ticket_id({"ticket.id": 717525}) == 717525
    assert IntegrationService.extract_ticket_id({"number": 717525}) == 717525
    assert IntegrationService.extract_ticket_id({"Número": 717525}) == 717525
    assert IntegrationService.extract_ticket_id({"ticketNumber": 717525}) == 717525
    assert IntegrationService.extract_ticket_id({"Ticket": {"Id": 717525}}) == 717525
    assert IntegrationService.extract_ticket_id({"ticket": {"id": 717525}}) == 717525
    assert IntegrationService.extract_ticket_id({"data": {"Id": 717525}}) == 717525


@pytest.mark.parametrize("blocked_status", ["Fechado", "Cancelado", "Resolvido", "Aguardando Informação"])
def test_validation_rejects_closed_statuses(blocked_status):
    service = IntegrationService.__new__(IntegrationService)
    ticket = make_valid_ticket(status=blocked_status)
    assert "status bloqueado" in service._validate_ticket(ticket)


def test_validation_accepts_valid_ticket():
    service = IntegrationService.__new__(IntegrationService)
    ticket = make_valid_ticket()
    assert service._validate_ticket(ticket) is None


def test_validation_rejects_filled_clickup_link():
    service = IntegrationService.__new__(IntegrationService)
    ticket = make_valid_ticket(custom_fields={"[BI] Criar tarefa no ClickUp?": "Sim", "[BI] Link ClickUp": "https://app.clickup.com/t/abc"})
    assert "Link ClickUp preenchido" in service._validate_ticket(ticket)


@pytest.mark.asyncio
async def test_duplicate_prevents_clickup_creation(db_session, monkeypatch):
    db_session.add(
        IntegrationLog(
            ticket_id=717525,
            ticket_subject="Melhoria no Dashboard",
            status=STATUS_CREATED,
            message="Criado anteriormente.",
        )
    )
    db_session.commit()

    async def fail_get_ticket(self, ticket_id):
        raise AssertionError("Movidesk nao deveria ser chamado para ticket duplicado.")

    monkeypatch.setattr(MovideskService, "get_ticket", fail_get_ticket)

    response = await IntegrationService(db_session).process_movidesk_webhook({"Id": 717525})

    assert response.success is True
    assert response.ticket_id == 717525
    assert "Nenhuma nova tarefa" in response.message


@pytest.mark.asyncio
async def test_missing_active_list_returns_controlled_error(db_session, monkeypatch):
    monkeypatch.delenv("CLICKUP_DEFAULT_LIST_ID", raising=False)
    get_settings.cache_clear()

    async def fake_get_ticket(self, ticket_id):
        return make_valid_ticket(id=ticket_id)

    async def fail_create_task(self, **kwargs):
        raise AssertionError("ClickUp nao deveria ser chamado sem lista ativa.")

    monkeypatch.setattr(MovideskService, "get_ticket", fake_get_ticket)
    monkeypatch.setattr(ClickUpService, "create_task", fail_create_task)

    response = await IntegrationService(db_session).process_movidesk_webhook({"Id": 717525})

    assert response.success is False
    assert response.ticket_id == 717525
    assert response.message == "Nenhuma lista mensal ativa do ClickUp cadastrada."
    assert db_session.query(IntegrationLog).filter(IntegrationLog.status == STATUS_ERROR_VALIDATION).count() == 1


@pytest.mark.asyncio
async def test_default_clickup_list_is_used_when_no_active_db_list(db_session, monkeypatch):
    monkeypatch.setenv("CLICKUP_DEFAULT_LIST_ID", "901327529184")
    monkeypatch.setenv("CLICKUP_DEFAULT_LIST_NAME", "Power BI")
    monkeypatch.setenv("CLICKUP_TASK_STATUS", "Open")
    monkeypatch.setenv("CLICKUP_ASSIGNEE_IDS", "123456")
    get_settings.cache_clear()
    created_payload = {}

    async def fake_get_ticket(self, ticket_id):
        return make_valid_ticket(id=ticket_id)

    async def fake_create_task(self, **kwargs):
        created_payload.update(kwargs)
        return {"id": "task-123", "url": "https://app.clickup.com/t/task-123"}

    monkeypatch.setattr(MovideskService, "get_ticket", fake_get_ticket)
    monkeypatch.setattr(ClickUpService, "create_task", fake_create_task)

    response = await IntegrationService(db_session).process_movidesk_webhook({"Id": 717525})

    get_settings.cache_clear()
    assert response.success is True
    assert response.clickup_task_id == "task-123"
    assert created_payload["list_id"] == "901327529184"
    assert created_payload["status"] == "Open"
    assert created_payload["assignee_ids"] == [123456]
