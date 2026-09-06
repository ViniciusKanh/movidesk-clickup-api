from app.services.movidesk_service import MovideskService


def test_parse_ticket_accepts_numeric_person_ids_and_action_author():
    payload = {
        "id": 123456,
        "subject": "Analytics request",
        "status": "Novo",
        "serviceFirstLevel": "Data",
        "serviceSecondLevel": "Analytics",
        "serviceThirdLevel": "Improvement",
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


def test_parse_ticket_extracts_category_urgency_tags_and_team():
    payload = {
        "id": 748598,
        "subject": "[ALERT] Possible error",
        "status": "Novo",
        "category": "Incidente",
        "urgency": "3 - Médio",
        "createdDate": "2026-09-02T10:42:00",
        "tags": ["#Filho", "#Escalation_GSI", ""],
        "clients": [{"id": 1}],
        "owner": {"id": 456, "team": "GSI-DEV"},
        "customFieldValues": [],
        "actions": [],
    }

    ticket = MovideskService()._parse_ticket(payload)

    assert ticket.category == "Incidente"
    assert ticket.urgency == "3 - Médio"
    assert ticket.created_date == "2026-09-02T10:42:00"
    assert ticket.tags == ["#Filho", "#Escalation_GSI"]
    assert ticket.owner_team == "GSI-DEV"
