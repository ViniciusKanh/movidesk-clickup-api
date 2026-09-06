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
        "id": 123456,
        "subject": "Dashboard improvement",
        "status": "Novo",
        "service_first_level": "Data",
        "service_second_level": "Analytics",
        "service_third_level": "Improvement",
        "owner_id": "agent-1",
        "owner_email": "vinicius.souza@penso.com.br",
        "owner_name": "Vinicius de Souza Santos",
        "custom_fields": {"[BI] Criar tarefa no ClickUp?": "Sim", "[BI] Link ClickUp": ""},
    }
    data.update(overrides)
    return MovideskTicket(**data)


def _service_for_owner_test() -> IntegrationService:
    service = IntegrationService.__new__(IntegrationService)
    service.settings = get_settings()
    return service


def test_owner_matches_by_id(monkeypatch):
    monkeypatch.setenv("MOVIDESK_REQUIRED_OWNER_ID", "agent-1")
    monkeypatch.delenv("MOVIDESK_REQUIRED_OWNER_EMAIL", raising=False)
    monkeypatch.delenv("MOVIDESK_REQUIRED_OWNER_NAME", raising=False)
    get_settings.cache_clear()

    service = _service_for_owner_test()
    ticket = make_valid_ticket(owner_id="agent-1", owner_email="outro@empresa.com")
    assert service._owner_matches(ticket) is True

    get_settings.cache_clear()


def test_owner_matches_by_email_when_no_id_configured(monkeypatch):
    monkeypatch.setenv("MOVIDESK_REQUIRED_OWNER_ID", "")
    monkeypatch.setenv("MOVIDESK_REQUIRED_OWNER_EMAIL", "Vinicius.Souza@Penso.com.br")
    monkeypatch.setenv("MOVIDESK_REQUIRED_OWNER_NAME", "")
    get_settings.cache_clear()

    service = _service_for_owner_test()
    ticket = make_valid_ticket(owner_id="agent-2", owner_email="vinicius.souza@penso.com.br  ")
    assert service._owner_matches(ticket) is True

    get_settings.cache_clear()


def test_owner_does_not_match():
    service = _service_for_owner_test()
    service.settings.movidesk_required_owner_id = "agent-1"
    service.settings.movidesk_required_owner_email = ""
    service.settings.movidesk_required_owner_name = ""
    ticket = make_valid_ticket(owner_id="agent-999")
    assert service._owner_matches(ticket) is False


def test_owner_check_disabled_when_nothing_configured(monkeypatch):
    # setenv com string vazia (nao delenv) para sobrepor um eventual valor vindo do .env local,
    # ja que env var tem prioridade sobre dotenv no pydantic-settings.
    monkeypatch.setenv("MOVIDESK_REQUIRED_OWNER_ID", "")
    monkeypatch.setenv("MOVIDESK_REQUIRED_OWNER_EMAIL", "")
    monkeypatch.setenv("MOVIDESK_REQUIRED_OWNER_NAME", "")
    get_settings.cache_clear()

    service = _service_for_owner_test()
    ticket = make_valid_ticket(owner_id=None, owner_email=None, owner_name=None)
    assert service._owner_matches(ticket) is True

    get_settings.cache_clear()


def test_extract_ticket_id_variations():
    assert IntegrationService.extract_ticket_id({"Id": 123456}) == 123456
    assert IntegrationService.extract_ticket_id({"id": "123456"}) == 123456
    assert IntegrationService.extract_ticket_id({"TicketId": 123456}) == 123456
    assert IntegrationService.extract_ticket_id({"ticketId": 123456}) == 123456
    assert IntegrationService.extract_ticket_id({"ticket_id": 123456}) == 123456
    assert IntegrationService.extract_ticket_id({"Ticket.Id": 123456}) == 123456
    assert IntegrationService.extract_ticket_id({"ticket.id": 123456}) == 123456
    assert IntegrationService.extract_ticket_id({"number": 123456}) == 123456
    assert IntegrationService.extract_ticket_id({"Número": 123456}) == 123456
    assert IntegrationService.extract_ticket_id({"ticketNumber": 123456}) == 123456
    assert IntegrationService.extract_ticket_id({"Ticket": {"Id": 123456}}) == 123456
    assert IntegrationService.extract_ticket_id({"ticket": {"id": 123456}}) == 123456
    assert IntegrationService.extract_ticket_id({"data": {"Id": 123456}}) == 123456


@pytest.mark.parametrize("blocked_status", ["Fechado", "Cancelado", "Resolvido", "Aguardando Informação"])
def test_validation_rejects_closed_statuses(blocked_status):
    service = IntegrationService.__new__(IntegrationService)
    ticket = make_valid_ticket(status=blocked_status)
    assert "status bloqueado" in service._validate_ticket(ticket)


def test_validation_accepts_valid_ticket():
    service = IntegrationService.__new__(IntegrationService)
    ticket = make_valid_ticket()
    assert service._validate_ticket(ticket) is None


def test_validation_rejects_service_when_required_service_is_configured(monkeypatch):
    monkeypatch.setenv("REQUIRED_SERVICE_FIRST_LEVEL", "Data")
    monkeypatch.setenv("REQUIRED_SERVICE_SECOND_LEVEL", "Analytics")
    monkeypatch.setenv("REQUIRED_SERVICE_THIRD_LEVEL", "Improvement")
    get_settings.cache_clear()

    service = IntegrationService.__new__(IntegrationService)
    service.settings = get_settings()
    ticket = make_valid_ticket(
        service_first_level="Support",
        service_second_level="Operations",
        service_third_level="Incident",
    )

    assert "servico esperado" in service._validate_ticket(ticket)
    get_settings.cache_clear()


def test_validation_rejects_filled_clickup_link():
    service = IntegrationService.__new__(IntegrationService)
    ticket = make_valid_ticket(custom_fields={"[BI] Criar tarefa no ClickUp?": "Sim", "[BI] Link ClickUp": "https://app.clickup.com/t/abc"})
    assert "Link ClickUp preenchido" in service._validate_ticket(ticket)


@pytest.mark.asyncio
async def test_duplicate_prevents_clickup_creation(db_session, monkeypatch):
    db_session.add(
        IntegrationLog(
            ticket_id=123456,
            ticket_subject="Dashboard improvement",
            status=STATUS_CREATED,
            message="Criado anteriormente.",
        )
    )
    db_session.commit()

    async def fail_get_ticket(self, ticket_id):
        raise AssertionError("Movidesk nao deveria ser chamado para ticket duplicado.")

    monkeypatch.setattr(MovideskService, "get_ticket", fail_get_ticket)

    response = await IntegrationService(db_session).process_movidesk_webhook({"Id": 123456})

    assert response.success is True
    assert response.ticket_id == 123456
    assert "Nenhuma nova tarefa" in response.message


@pytest.mark.asyncio
async def test_missing_active_list_returns_controlled_error(db_session, monkeypatch):
    monkeypatch.setenv("CLICKUP_DEFAULT_LIST_ID", "")
    monkeypatch.setenv("MOVIDESK_REQUIRED_OWNER_ID", "")
    monkeypatch.setenv("MOVIDESK_REQUIRED_OWNER_EMAIL", "")
    monkeypatch.setenv("MOVIDESK_REQUIRED_OWNER_NAME", "")
    get_settings.cache_clear()

    async def fake_get_ticket(self, ticket_id):
        return make_valid_ticket(id=ticket_id)

    async def fail_create_task(self, **kwargs):
        raise AssertionError("ClickUp nao deveria ser chamado sem lista ativa.")

    monkeypatch.setattr(MovideskService, "get_ticket", fake_get_ticket)
    monkeypatch.setattr(ClickUpService, "create_task", fail_create_task)

    response = await IntegrationService(db_session).process_movidesk_webhook({"Id": 123456})

    assert response.success is False
    assert response.ticket_id == 123456
    assert response.message == "Nenhuma lista mensal ativa do ClickUp cadastrada."
    assert db_session.query(IntegrationLog).filter(IntegrationLog.status == STATUS_ERROR_VALIDATION).count() == 1


@pytest.mark.asyncio
async def test_webhook_ignores_ticket_when_owner_does_not_match(db_session, monkeypatch):
    monkeypatch.setenv("MOVIDESK_REQUIRED_OWNER_EMAIL", "vinicius.souza@penso.com.br")
    get_settings.cache_clear()

    async def fake_get_ticket(self, ticket_id):
        return make_valid_ticket(id=ticket_id, owner_email="outra.pessoa@penso.com.br")

    async def fail_create_task(self, **kwargs):
        raise AssertionError("ClickUp nao deveria ser chamado quando o responsavel nao bate.")

    monkeypatch.setattr(MovideskService, "get_ticket", fake_get_ticket)
    monkeypatch.setattr(ClickUpService, "create_task", fail_create_task)

    response = await IntegrationService(db_session).process_movidesk_webhook({"Id": 123456})

    get_settings.cache_clear()
    assert response.success is False
    assert "responsavel" in response.message.lower()
    from app.services.integration_service import STATUS_IGNORED_OWNER

    assert db_session.query(IntegrationLog).filter(IntegrationLog.status == STATUS_IGNORED_OWNER).count() == 1


@pytest.mark.asyncio
async def test_default_clickup_list_is_used_when_no_active_db_list(db_session, monkeypatch):
    monkeypatch.setenv("CLICKUP_DEFAULT_LIST_ID", "1234567890")
    monkeypatch.setenv("CLICKUP_DEFAULT_LIST_NAME", "Analytics Requests")
    monkeypatch.setenv("CLICKUP_TASK_STATUS", "Open")
    monkeypatch.setenv("CLICKUP_ASSIGNEE_IDS", "123456")
    monkeypatch.setenv("MOVIDESK_REQUIRED_OWNER_ID", "")
    monkeypatch.setenv("MOVIDESK_REQUIRED_OWNER_EMAIL", "")
    monkeypatch.setenv("MOVIDESK_REQUIRED_OWNER_NAME", "")
    get_settings.cache_clear()
    created_payload = {}

    async def fake_get_ticket(self, ticket_id):
        return make_valid_ticket(id=ticket_id)

    async def fake_create_task(self, **kwargs):
        created_payload.update(kwargs)
        return {"id": "task-123", "url": "https://app.clickup.com/t/task-123"}

    monkeypatch.setattr(MovideskService, "get_ticket", fake_get_ticket)
    monkeypatch.setattr(ClickUpService, "create_task", fake_create_task)

    response = await IntegrationService(db_session).process_movidesk_webhook({"Id": 123456})

    get_settings.cache_clear()
    assert response.success is True
    assert response.clickup_task_id == "task-123"
    assert created_payload["list_id"] == "1234567890"
    assert created_payload["status"] == "Open"
    assert created_payload["assignee_ids"] == [123456]


@pytest.mark.asyncio
async def test_diagnose_ticket_would_create_task(db_session, monkeypatch):
    monkeypatch.setenv("CLICKUP_DEFAULT_LIST_ID", "1234567890")
    monkeypatch.setenv("CLICKUP_DEFAULT_LIST_NAME", "Analytics Requests")
    monkeypatch.setenv("MOVIDESK_REQUIRED_OWNER_EMAIL", "vinicius.souza@penso.com.br")
    monkeypatch.delenv("MOVIDESK_REQUIRED_OWNER_ID", raising=False)
    monkeypatch.delenv("MOVIDESK_REQUIRED_OWNER_NAME", raising=False)
    get_settings.cache_clear()

    async def fake_get_ticket(self, ticket_id):
        return make_valid_ticket(id=ticket_id)

    monkeypatch.setattr(MovideskService, "get_ticket", fake_get_ticket)

    result = await IntegrationService(db_session).diagnose_ticket(123456)

    get_settings.cache_clear()
    assert result["found"] is True
    assert result["owner_matches"] is True
    assert result["validation_error"] is None
    assert result["active_clickup_list_id"] == "1234567890"
    assert result["would_create_task"] is True
    assert result["already_integrated"] is False


@pytest.mark.asyncio
async def test_diagnose_ticket_owner_does_not_match(db_session, monkeypatch):
    monkeypatch.setenv("MOVIDESK_REQUIRED_OWNER_EMAIL", "vinicius.souza@penso.com.br")
    get_settings.cache_clear()

    async def fake_get_ticket(self, ticket_id):
        return make_valid_ticket(id=ticket_id, owner_email="outra.pessoa@penso.com.br")

    monkeypatch.setattr(MovideskService, "get_ticket", fake_get_ticket)

    result = await IntegrationService(db_session).diagnose_ticket(123456)

    get_settings.cache_clear()
    assert result["owner_matches"] is False
    assert result["would_create_task"] is False
    assert "responsavel" in result["verdict"].lower()


@pytest.mark.asyncio
async def test_diagnose_ticket_already_integrated(db_session, monkeypatch):
    db_session.add(
        IntegrationLog(
            ticket_id=123456,
            ticket_subject="Dashboard improvement",
            status=STATUS_CREATED,
            clickup_task_id="task-1",
            clickup_task_url="https://app.clickup.com/t/task-1",
            message="Criado anteriormente.",
        )
    )
    db_session.commit()

    async def fake_get_ticket(self, ticket_id):
        return make_valid_ticket(id=ticket_id)

    monkeypatch.setattr(MovideskService, "get_ticket", fake_get_ticket)

    result = await IntegrationService(db_session).diagnose_ticket(123456)

    assert result["already_integrated"] is True
    assert result["existing_clickup_task_id"] == "task-1"
    assert result["would_create_task"] is False


@pytest.mark.asyncio
async def test_diagnose_ticket_not_found(db_session, monkeypatch):
    from app.services.movidesk_service import MovideskServiceError

    async def fake_get_ticket(self, ticket_id):
        raise MovideskServiceError(f"Ticket {ticket_id} nao encontrado no Movidesk.")

    monkeypatch.setattr(MovideskService, "get_ticket", fake_get_ticket)

    result = await IntegrationService(db_session).diagnose_ticket(999999)

    assert result["found"] is False
    assert "nao encontrado" in result["error"]
