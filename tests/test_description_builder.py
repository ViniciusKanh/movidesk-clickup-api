from app.config import get_settings
from app.schemas import MovideskAction, MovideskTicket
from app.services.description_builder import build_clickup_description, build_clickup_task_name


def test_task_name_contains_ticket_id_and_subject():
    ticket = MovideskTicket(raw={}, id=123456, subject="Analytics request")
    assert build_clickup_task_name(ticket) == "[MOVI-123456] Analytics request"


def test_description_uses_markdown_headings_and_bullets():
    ticket = MovideskTicket(
        raw={},
        id=123456,
        subject="Analytics request",
        requester_name="Sample requester",
        service_first_level="Data",
        service_second_level="Analytics",
        service_third_level="Improvement",
        custom_fields={
            "[BI] Área solicitante": "Operations",
            "[BI] Tipo de demanda": "Improvement",
            "[BI] Nome do dashboard/projeto": "Executive dashboard",
            "[BI] Problema atual": "Daily totals are not matching the source system.",
            "[BI] Resultado esperado": "Show validated daily totals by business unit.",
            "Additional field": "Relevant extra value",
        },
        actions=[
            MovideskAction(
                raw={},
                created_date="2026-06-11T10:00:00",
                created_by_name="Sample Agent",
                type="Comment",
                description="Ticket action registered for the analytics team.",
            )
        ],
    )
    description = build_clickup_description(ticket)

    assert "## 📋 Resumo da demanda" in description
    assert "## 🎫 Origem" in description
    assert "**Ticket Movidesk:** #123456" in description
    assert "**Área solicitante:** Operations" in description
    assert "## 🧭 Dados de BI preenchidos no Movidesk" in description
    assert "**Additional field:** Relevant extra value" in description
    assert "## 🕘 Últimas ações do ticket" in description
    assert "Ticket action registered for the analytics team." in description
    assert "[Não informado]" not in description
    assert "CHECKLIST TECNICO" not in description
    assert "- [ ]" not in description


def test_description_includes_richer_movidesk_fields():
    ticket = MovideskTicket(
        raw={},
        id=123456,
        subject="Analytics request",
        status="Novo",
        category="Incidente",
        urgency="3 - Médio",
        tags=["#Filho", "#Escalation_GSI"],
        created_date="2026-09-02T10:42:00",
        owner_team="GSI-DEV",
        requester_name="Sample requester",
    )
    description = build_clickup_description(ticket)

    assert "**Categoria:** Incidente" in description
    assert "**Urgência:** 3 - Médio" in description
    assert "**Data de abertura:** 2026-09-02T10:42:00" in description
    assert "**Equipe responsável:** GSI-DEV" in description
    assert "**Tags:** #Filho, #Escalation_GSI" in description


def test_ticket_url_ignores_misconfigured_template_without_placeholder(monkeypatch):
    """Se MOVIDESK_TICKET_URL_TEMPLATE estiver mal configurado (ex.: um GUID solto,
    sem o placeholder {ticket_id}), a descricao nao deve mostrar esse valor como link."""
    monkeypatch.setenv("MOVIDESK_TICKET_URL_TEMPLATE", "d034f39e-ecf2-4b35-89a4-4dd8c718d5e4")
    get_settings.cache_clear()

    ticket = MovideskTicket(raw={}, id=748598, subject="Teste")
    description = build_clickup_description(ticket)

    get_settings.cache_clear()
    assert "d034f39e" not in description
    assert "**Link:**" not in description


def test_ticket_url_applies_valid_template(monkeypatch):
    monkeypatch.setenv("MOVIDESK_TICKET_URL_TEMPLATE", "https://penso.movidesk.com/Ticket/Edit/{ticket_id}")
    get_settings.cache_clear()

    ticket = MovideskTicket(raw={}, id=748598, subject="Teste")
    description = build_clickup_description(ticket)

    get_settings.cache_clear()
    assert "[Abrir no Movidesk](https://penso.movidesk.com/Ticket/Edit/748598)" in description


def test_sections_are_separated_by_divider():
    ticket = MovideskTicket(raw={}, id=1, subject="Teste", requester_name="Alguem")
    description = build_clickup_description(ticket)
    assert "\n\n---\n\n" in description
