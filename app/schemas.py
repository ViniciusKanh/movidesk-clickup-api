from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "movidesk-clickup-api"


class WebhookResponse(BaseModel):
    success: bool
    message: str
    ticket_id: int | None = None
    clickup_task_id: str | None = None
    clickup_task_url: str | None = None


class ClickUpMonthlyListBase(BaseModel):
    year: int = Field(..., ge=2000, le=2100)
    month_number: int = Field(..., ge=1, le=12)
    month_name: str = Field(..., min_length=3, max_length=30)
    clickup_folder_id: str | None = Field(default=None, max_length=80)
    clickup_folder_name: str | None = Field(default=None, max_length=120)
    clickup_list_name: str = Field(..., min_length=1, max_length=120)
    clickup_list_id: str = Field(..., min_length=1, max_length=80)
    active: bool = False


class ClickUpMonthlyListCreate(ClickUpMonthlyListBase):
    pass


class ClickUpMonthlyListResponse(ClickUpMonthlyListBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ClickUpFolderListItem(BaseModel):
    id: str
    name: str | None = None


class ClickUpBrowseItem(BaseModel):
    """Item generico para navegacao Workspace -> Space -> Folder no ClickUp (somente leitura)."""

    id: str
    name: str | None = None


class ClickUpFolderSetupRequest(BaseModel):
    """Fluxo simplificado do painel: informar a pasta e a lista escolhida dentro dela.

    O ano/mes/nome do mes sao preenchidos automaticamente com a data atual do servidor,
    e a lista informada e ativada automaticamente (desativando as demais).
    """

    clickup_folder_id: str = Field(..., min_length=1, max_length=80)
    clickup_folder_name: str | None = Field(default=None, max_length=120)
    clickup_list_id: str = Field(..., min_length=1, max_length=80)
    clickup_list_name: str = Field(..., min_length=1, max_length=120)


class AdminLoginRequest(BaseModel):
    username: str
    password: str


class AdminLoginResponse(BaseModel):
    success: bool = True


class MovideskIntegrationStatus(BaseModel):
    configured: bool
    base_url: str
    owner_rule: str
    owner_value: str | None = None
    read_only: bool = True


class ClickUpIntegrationStatus(BaseModel):
    configured: bool
    base_url: str
    default_list_id: str | None = None
    default_list_name: str | None = None
    active_list_name: str | None = None
    assignee_mode: str
    task_status: str | None = None


class IntegrationsStatusResponse(BaseModel):
    movidesk: MovideskIntegrationStatus
    clickup: ClickUpIntegrationStatus


class ConnectionTestResult(BaseModel):
    """Resultado de um teste de conexao (sempre via GET, nunca escreve nada)."""

    ok: bool
    message: str


class IntegrationLogResponse(BaseModel):
    id: int
    ticket_id: int | None
    ticket_subject: str | None
    clickup_task_id: str | None
    clickup_task_url: str | None
    status: str
    message: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class TicketDiagnosticResponse(BaseModel):
    """Diagnostico somente leitura de elegibilidade de um ticket.

    Reutiliza exatamente as mesmas checagens do fluxo real do webhook (responsavel,
    validacao, lista ativa), mas nunca cria tarefa no ClickUp nem altera nada no
    Movidesk. Serve para o usuario entender, para um ticket especifico, por que a
    integracao criaria ou nao criaria uma tarefa.
    """

    ticket_id: int
    found: bool
    error: str | None = None
    subject: str | None = None
    status: str | None = None
    already_integrated: bool = False
    existing_clickup_task_id: str | None = None
    existing_clickup_task_url: str | None = None
    owner_rule: str | None = None
    owner_required_value: str | None = None
    owner_id: str | None = None
    owner_email: str | None = None
    owner_name: str | None = None
    owner_matches: bool | None = None
    service_first_level: str | None = None
    service_second_level: str | None = None
    service_third_level: str | None = None
    custom_field_criar_tarefa: Any = None
    custom_field_link_clickup: Any = None
    validation_error: str | None = None
    active_clickup_list_id: str | None = None
    active_clickup_list_name: str | None = None
    would_create_task: bool = False
    verdict: str


class MovideskAction(BaseModel):
    raw: dict[str, Any]
    id: int | str | None = None
    type: str | None = None
    origin: str | None = None
    status: str | None = None
    created_date: str | None = None
    created_by_name: str | None = None
    description: str | None = None


class MovideskTicket(BaseModel):
    raw: dict[str, Any]
    id: int
    subject: str
    status: str | None = None
    service_first_level: str | None = None
    service_second_level: str | None = None
    service_third_level: str | None = None
    requester_name: str | None = None
    owner_id: str | None = None
    owner_email: str | None = None
    owner_name: str | None = None
    custom_fields: dict[str, Any] = Field(default_factory=dict)
    actions: list[MovideskAction] = Field(default_factory=list)
