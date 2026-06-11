from app.services.movidesk_service import MovideskService


def test_parse_ticket_accepts_numeric_person_ids_and_action_author():
    payload = {
        "id": 717525,
        "subject": "Teste BI",
        "status": "Novo",
        "serviceFirstLevel": "GSI",
        "serviceSecondLevel": "BI",
        "serviceThirdLevel": "Melhoria/Projeto",
        "clients": [{"id": 123}],
        "owner": {"id": 456},
        "customFieldValues": [],
        "actions": [
            {
                "id": 1,
                "type": 2,
                "createdDate": "2026-06-11T10:00:00",
                "createdBy": {"id": 789},
                "description": "<p>Acao de teste</p>",
            }
        ],
    }

    ticket = MovideskService()._parse_ticket(payload)

    assert ticket.requester_name == "123"
    assert ticket.owner_name == "456"
    assert ticket.actions[0].created_by_name == "789"
    assert ticket.actions[0].type == "2"
