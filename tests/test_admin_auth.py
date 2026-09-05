from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app


def _client() -> TestClient:
    # base_url https para o cookie de sessao (secure=True) ser aceito pelo cliente de teste.
    return TestClient(app, base_url="https://testserver")


def test_admin_routes_require_login_when_configured(monkeypatch):
    monkeypatch.setenv("ADMIN_USERNAME", "vinicius")
    monkeypatch.setenv("ADMIN_PASSWORD", "senha-forte")
    monkeypatch.setenv("ADMIN_SESSION_SECRET", "test-secret")
    get_settings.cache_clear()

    response = _client().get("/admin/clickup-lists")

    get_settings.cache_clear()
    assert response.status_code == 401


def test_admin_routes_disabled_without_credentials_configured(monkeypatch):
    # setenv com string vazia (nao delenv) para sobrepor um eventual valor vindo do .env local.
    monkeypatch.setenv("ADMIN_USERNAME", "")
    monkeypatch.setenv("ADMIN_PASSWORD", "")
    get_settings.cache_clear()

    response = _client().get("/admin/clickup-lists")

    get_settings.cache_clear()
    assert response.status_code == 503


def test_login_with_wrong_password_is_rejected(monkeypatch):
    monkeypatch.setenv("ADMIN_USERNAME", "vinicius")
    monkeypatch.setenv("ADMIN_PASSWORD", "senha-forte")
    monkeypatch.setenv("ADMIN_SESSION_SECRET", "test-secret")
    get_settings.cache_clear()

    response = _client().post("/admin/login", json={"username": "vinicius", "password": "errada"})

    get_settings.cache_clear()
    assert response.status_code == 401


def test_login_then_access_protected_route(monkeypatch):
    monkeypatch.setenv("ADMIN_USERNAME", "vinicius")
    monkeypatch.setenv("ADMIN_PASSWORD", "senha-forte")
    monkeypatch.setenv("ADMIN_SESSION_SECRET", "test-secret")
    get_settings.cache_clear()

    with _client() as client:
        login_response = client.post("/admin/login", json={"username": "vinicius", "password": "senha-forte"})
        assert login_response.status_code == 200

        protected_response = client.get("/admin/clickup-lists")
        assert protected_response.status_code == 200

    get_settings.cache_clear()


def test_logout_clears_session(monkeypatch):
    monkeypatch.setenv("ADMIN_USERNAME", "vinicius")
    monkeypatch.setenv("ADMIN_PASSWORD", "senha-forte")
    monkeypatch.setenv("ADMIN_SESSION_SECRET", "test-secret")
    get_settings.cache_clear()

    with _client() as client:
        client.post("/admin/login", json={"username": "vinicius", "password": "senha-forte"})
        client.post("/admin/logout")

        response = client.get("/admin/clickup-lists")
        assert response.status_code == 401

    get_settings.cache_clear()
