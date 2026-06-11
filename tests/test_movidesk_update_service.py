from app.schemas import MovideskTicket
from app.services.movidesk_update_service import MovideskClickUpUpdatePayload, MovideskUpdateService


def test_build_custom_field_values_updates_clickup_fields_and_preserves_existing_fields():
    ticket = MovideskTicket(
        raw={
            "customFieldValues": [
                {
                    "customFieldId": 1,
                    "customFieldRuleId": 10,
                    "line": 1,
                    "customField": {"name": "[BI] ID ClickUp"},
                    "value": "",
                    "items": [],
                },
                {
                    "customFieldId": 2,
                    "customFieldRuleId": 10,
                    "line": 1,
                    "customField": {"name": "[BI] Link ClickUp"},
                    "value": "",
                    "items": [],
                },
                {
                    "customFieldId": 3,
                    "customFieldRuleId": 10,
                    "line": 1,
                    "customField": {"name": "[BI] Status integração ClickUp"},
                    "value": None,
                    "items": [],
                },
                {
                    "customFieldId": 4,
                    "customFieldRuleId": 10,
                    "line": 1,
                    "customField": {"name": "[BI] Mensagem erro integração"},
                    "value": "erro antigo",
                    "items": [],
                },
                {
                    "customFieldId": 5,
                    "customFieldRuleId": 10,
                    "line": 1,
                    "customField": {"name": "[BI] Tipo de demanda"},
                    "value": None,
                    "items": [{"customFieldItem": "Melhoria"}],
                },
            ]
        },
        id=123456,
        subject="Analytics request",
    )
    payload = MovideskClickUpUpdatePayload(
        ticket_id=123456,
        clickup_task_id="86aj09w3f",
        clickup_task_url="https://app.clickup.com/t/86aj09w3f",
        status_integracao="OK",
        mensagem="",
    )

    fields = MovideskUpdateService()._build_custom_field_values(ticket, payload)

    assert fields[0]["value"] == "86aj09w3f"
    assert fields[1]["value"] == "https://app.clickup.com/t/86aj09w3f"
    assert fields[2]["items"] == [{"customFieldItem": "OK"}]
    assert fields[3]["value"] == ""
    assert fields[4]["items"] == [{"customFieldItem": "Melhoria"}]
