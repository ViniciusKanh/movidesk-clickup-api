import httpx
import pytest

from app.config import get_settings
from app.services.clickup_service import ClickUpService, ClickUpServiceError


class _FakeResponse:
    def __init__(self, status_code: int, json_data):
        self.status_code = status_code
        self._json_data = json_data

    def json(self):
        return self._json_data


class _FakeAsyncClient:
    def __init__(self, response: _FakeResponse):
        self._response = response

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def get(self, *args, **kwargs):
        return self._response

    async def post(self, *args, **kwargs):
        return self._response


@pytest.mark.asyncio
async def test_folder_resolves_list(monkeypatch):
    monkeypatch.setenv("CLICKUP_TOKEN", "fake-token")
    get_settings.cache_clear()

    fake_response = _FakeResponse(200, {"lists": [{"id": 111, "name": "Lista A"}, {"id": 222, "name": "Lista B"}]})
    monkeypatch.setattr(httpx, "AsyncClient", lambda *a, **k: _FakeAsyncClient(fake_response))

    service = ClickUpService()
    lists = await service.get_folder_lists("999")

    assert lists == [{"id": "111", "name": "Lista A"}, {"id": "222", "name": "Lista B"}]
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_folder_without_lists_returns_empty(monkeypatch):
    monkeypatch.setenv("CLICKUP_TOKEN", "fake-token")
    get_settings.cache_clear()

    fake_response = _FakeResponse(200, {"lists": []})
    monkeypatch.setattr(httpx, "AsyncClient", lambda *a, **k: _FakeAsyncClient(fake_response))

    service = ClickUpService()
    lists = await service.get_folder_lists("999")

    assert lists == []
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_folder_lists_raises_on_http_error(monkeypatch):
    monkeypatch.setenv("CLICKUP_TOKEN", "fake-token")
    get_settings.cache_clear()

    fake_response = _FakeResponse(404, {})
    monkeypatch.setattr(httpx, "AsyncClient", lambda *a, **k: _FakeAsyncClient(fake_response))

    service = ClickUpService()
    with pytest.raises(ClickUpServiceError):
        await service.get_folder_lists("999")

    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_get_teams_returns_workspaces(monkeypatch):
    monkeypatch.setenv("CLICKUP_TOKEN", "fake-token")
    get_settings.cache_clear()

    fake_response = _FakeResponse(200, {"teams": [{"id": 1, "name": "Espaco de trabalho Penso"}]})
    monkeypatch.setattr(httpx, "AsyncClient", lambda *a, **k: _FakeAsyncClient(fake_response))

    service = ClickUpService()
    teams = await service.get_teams()

    assert teams == [{"id": "1", "name": "Espaco de trabalho Penso"}]
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_get_spaces_returns_spaces(monkeypatch):
    monkeypatch.setenv("CLICKUP_TOKEN", "fake-token")
    get_settings.cache_clear()

    fake_response = _FakeResponse(200, {"spaces": [{"id": 10, "name": "GSI"}]})
    monkeypatch.setattr(httpx, "AsyncClient", lambda *a, **k: _FakeAsyncClient(fake_response))

    service = ClickUpService()
    spaces = await service.get_spaces("1")

    assert spaces == [{"id": "10", "name": "GSI"}]
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_get_folders_returns_folders_not_lists(monkeypatch):
    monkeypatch.setenv("CLICKUP_TOKEN", "fake-token")
    get_settings.cache_clear()

    fake_response = _FakeResponse(200, {"folders": [{"id": 20, "name": "2026"}]})
    monkeypatch.setattr(httpx, "AsyncClient", lambda *a, **k: _FakeAsyncClient(fake_response))

    service = ClickUpService()
    folders = await service.get_folders("10")

    assert folders == [{"id": "20", "name": "2026"}]
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_get_folders_raises_on_http_error(monkeypatch):
    monkeypatch.setenv("CLICKUP_TOKEN", "fake-token")
    get_settings.cache_clear()

    fake_response = _FakeResponse(401, {})
    monkeypatch.setattr(httpx, "AsyncClient", lambda *a, **k: _FakeAsyncClient(fake_response))

    service = ClickUpService()
    with pytest.raises(ClickUpServiceError):
        await service.get_folders("10")

    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_create_task_error_includes_clickup_detail(monkeypatch):
    """Erros 400 do ClickUp (ex.: status invalido para a lista) devem trazer o
    motivo exato no ClickUpServiceError, para aparecer no log sem precisar adivinhar."""
    monkeypatch.setenv("CLICKUP_TOKEN", "fake-token")
    get_settings.cache_clear()

    fake_response = _FakeResponse(400, {"err": "Status not found", "ECODE": "ITEM_046"})
    monkeypatch.setattr(httpx, "AsyncClient", lambda *a, **k: _FakeAsyncClient(fake_response))

    service = ClickUpService()
    with pytest.raises(ClickUpServiceError) as exc_info:
        await service.create_task(list_id="999", name="Teste", description="Teste", status="Open")

    assert "Status not found" in str(exc_info.value)
    assert "ITEM_046" in str(exc_info.value)
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_create_task_error_without_detail_still_reports_http_status(monkeypatch):
    monkeypatch.setenv("CLICKUP_TOKEN", "fake-token")
    get_settings.cache_clear()

    fake_response = _FakeResponse(500, {})
    monkeypatch.setattr(httpx, "AsyncClient", lambda *a, **k: _FakeAsyncClient(fake_response))

    service = ClickUpService()
    with pytest.raises(ClickUpServiceError) as exc_info:
        await service.create_task(list_id="999", name="Teste", description="Teste")

    assert "HTTP 500" in str(exc_info.value)
    get_settings.cache_clear()
