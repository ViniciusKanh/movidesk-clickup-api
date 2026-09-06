from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app


def test_invalid_webhook_secret_returns_401(monkeypatch):
    monkeypatch.setenv("WEBHOOK_SECRET", "expected-secret")
    get_settings.cache_clear()

    response = TestClient(app).post(
        "/webhooks/movidesk/clickup",
        json={"Id": 123456},
        headers={"X-Webhook-Secret": "wrong-secret"},
    )

    get_settings.cache_clear()
    assert response.status_code == 401
    assert response.json()["detail"] == "Nao autorizado."


def test_webhook_secret_accepted_via_query_string(monkeypatch):
    """O Movidesk (acao 'Acionar Webhook' dos gatilhos) so tem campo de URL,
    sem suporte a cabecalhos customizados. Por isso o segredo tambem pode ser
    enviado como ?secret=... na propria URL configurada no gatilho."""
    monkeypatch.setenv("WEBHOOK_SECRET", "expected-secret")
    get_settings.cache_clear()

    response = TestClient(app).post(
        "/webhooks/movidesk/clickup?secret=expected-secret",
        json={"Id": 123456},
    )

    get_settings.cache_clear()
    assert response.status_code != 401


def test_invalid_webhook_secret_via_query_string_returns_401(monkeypatch):
    monkeypatch.setenv("WEBHOOK_SECRET", "expected-secret")
    get_settings.cache_clear()

    response = TestClient(app).post(
        "/webhooks/movidesk/clickup?secret=wrong-secret",
        json={"Id": 123456},
    )

    get_settings.cache_clear()
    assert response.status_code == 401
    assert response.json()["detail"] == "Nao autorizado."


def test_header_takes_priority_over_query_string(monkeypatch):
    monkeypatch.setenv("WEBHOOK_SECRET", "expected-secret")
    get_settings.cache_clear()

    response = TestClient(app).post(
        "/webhooks/movidesk/clickup?secret=expected-secret",
        json={"Id": 123456},
        headers={"X-Webhook-Secret": "wrong-secret"},
    )

    get_settings.cache_clear()
    assert response.status_code == 401
