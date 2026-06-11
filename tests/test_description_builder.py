from app.schemas import MovideskAction, MovideskTicket
from app.services.description_builder import build_clickup_description, build_clickup_task_name


def test_task_name_contains_ticket_id_and_subject():
    ticket = MovideskTicket(raw={}, id=123456, subject="Analytics request")
    assert build_clickup_task_name(ticket) == "[MOVI-123456] Analytics request"


def test_description_is_plain_text_without_markdown_headers():
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
    assert "RESUMO DA DEMANDA" in description
    assert "##" not in description
    assert "Ticket Movidesk: 123456" in description
    assert "Área solicitante: Operations." in description
    assert "DADOS DE BI PREENCHIDOS NO MOVIDESK" in description
    assert "Additional field: Relevant extra value" in description
    assert "ULTIMAS ACOES DO TICKET" in description
    assert "Ticket action registered for the analytics team." in description
    assert "[Não informado]" not in description
