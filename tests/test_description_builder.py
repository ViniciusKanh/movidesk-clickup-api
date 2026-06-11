from app.schemas import MovideskAction, MovideskTicket
from app.services.description_builder import build_clickup_description, build_clickup_task_name


def test_task_name_contains_ticket_id_and_subject():
    ticket = MovideskTicket(raw={}, id=717525, subject="Teste BI")
    assert build_clickup_task_name(ticket) == "[MOVI-717525] Teste BI"


def test_description_is_plain_text_without_markdown_headers():
    ticket = MovideskTicket(
        raw={},
        id=717525,
        subject="Teste BI",
        requester_name="Solicitante Teste",
        service_first_level="GSI",
        service_second_level="BI",
        service_third_level="Melhoria/Projeto",
        custom_fields={
            "[BI] Área solicitante": "Dados",
            "[BI] Tipo de demanda": "Melhoria",
            "[BI] Nome do dashboard/projeto": "Satisfação Salesforce V2",
            "[BI] Problema atual": "Relacionamentos não aparecem por dia.",
            "[BI] Resultado esperado": "Visualizar relacionamentos concluídos por dia.",
            "Campo adicional livre": "Valor adicional importante",
        },
        actions=[
            MovideskAction(
                raw={},
                created_date="2026-06-11T10:00:00",
                created_by_name="Vinicius Santos",
                type="Comentário",
                description="Ação registrada no Movidesk para BI.",
            )
        ],
    )
    description = build_clickup_description(ticket)
    assert "RESUMO DA DEMANDA" in description
    assert "##" not in description
    assert "Ticket Movidesk: 717525" in description
    assert "Área solicitante: Dados." in description
    assert "DADOS DE BI PREENCHIDOS NO MOVIDESK" in description
    assert "Campo adicional livre: Valor adicional importante" in description
    assert "ULTIMAS ACOES DO TICKET" in description
    assert "Ação registrada no Movidesk para BI." in description
    assert "[Não informado]" not in description
