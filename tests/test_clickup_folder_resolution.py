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
