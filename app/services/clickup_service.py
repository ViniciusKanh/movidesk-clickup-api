from typing import Any

import httpx

from app.config import get_settings


class ClickUpServiceError(Exception):
    pass


class ClickUpService:
    """Cliente HTTP para o ClickUp.

    SEGURANCA: esta classe so tem uma operacao de escrita - create_task (cria
    uma tarefa NOVA). Nao existe (e nao deve ser adicionado sem pedido
    explicito) nenhum metodo de update/delete de tarefas existentes, o que
    evita qualquer risco de alterar ou apagar tarefas de outras pessoas na
    mesma pasta/lista. As demais chamadas (get_authorized_user,
    get_folder_lists, get_list, get_list_member_id_by_email) sao apenas
    leitura, usadas para resolver a lista/assignee corretos antes de criar.
    """

    def __init__(self) -> None:
        self.settings = get_settings()

    async def create_task(
        self,
        list_id: str,
        name: str,
        description: str,
        tags: list[str] | None = None,
        assignee_ids: list[int] | None = None,
        status: str | None = None,
    ) -> dict[str, Any]:
        if not self.settings.clickup_token:
            raise ClickUpServiceError("CLICKUP_TOKEN nao configurado.")

        url = f"{self.settings.clickup_base_url.rstrip('/')}/list/{list_id}/task"
        headers = {
            "Authorization": self.settings.clickup_token,
            "Content-Type": "application/json",
        }
        payload = {
            "name": name,
            "description": description,
            "tags": tags or ["movidesk", "bi", "melhoria-projeto"],
        }
        if status:
            payload["status"] = status
        if assignee_ids:
            payload["assignees"] = assignee_ids

        try:
            async with httpx.AsyncClient(timeout=self.settings.request_timeout_seconds) as client:
                response = await client.post(url, headers=headers, json=payload)
        except httpx.HTTPError:
            raise ClickUpServiceError("Erro de comunicacao ao criar tarefa no ClickUp.") from None

        if response.status_code >= 400:
            raise ClickUpServiceError(f"Erro ao criar tarefa no ClickUp. HTTP {response.status_code}.")

        try:
            data = response.json()
        except ValueError:
            raise ClickUpServiceError("Resposta inesperada da API do ClickUp.") from None

        task_id = data.get("id")
        task_url = data.get("url") or data.get("link")

        if not task_id:
            raise ClickUpServiceError("ClickUp retornou resposta sem ID de tarefa.")

        return {
            "id": str(task_id),
            "url": task_url,
            "raw": data,
        }

    async def get_authorized_user(self) -> dict[str, Any] | None:
        if not self.settings.clickup_token:
            raise ClickUpServiceError("CLICKUP_TOKEN nao configurado.")

        url = f"{self.settings.clickup_base_url.rstrip('/')}/user"
        headers = {"Authorization": self.settings.clickup_token}

        try:
            async with httpx.AsyncClient(timeout=self.settings.request_timeout_seconds) as client:
                response = await client.get(url, headers=headers)
        except httpx.HTTPError:
            return None

        if response.status_code >= 400:
            return None

        data = response.json()
        user = data.get("user")
        return user if isinstance(user, dict) else None

    async def get_folder_lists(self, folder_id: str) -> list[dict[str, Any]]:
        """Retorna as listas existentes dentro de uma pasta (Folder) do ClickUp.

        Usado para resolver corretamente Folder ID -> List ID, ja que a API de
        criacao de tarefa exige uma List ID (nunca um Folder ID).
        """
        if not self.settings.clickup_token:
            raise ClickUpServiceError("CLICKUP_TOKEN nao configurado.")

        url = f"{self.settings.clickup_base_url.rstrip('/')}/folder/{folder_id}/list"
        headers = {"Authorization": self.settings.clickup_token}

        try:
            async with httpx.AsyncClient(timeout=self.settings.request_timeout_seconds) as client:
                response = await client.get(url, headers=headers, params={"archived": "false"})
        except httpx.HTTPError:
            raise ClickUpServiceError("Erro de comunicacao ao consultar listas da pasta no ClickUp.") from None

        if response.status_code >= 400:
            raise ClickUpServiceError(f"Erro ao consultar listas da pasta no ClickUp. HTTP {response.status_code}.")

        try:
            data = response.json()
        except ValueError:
            raise ClickUpServiceError("Resposta inesperada da API do ClickUp.") from None

        lists = data.get("lists") if isinstance(data, dict) else None
        if not isinstance(lists, list):
            return []

        return [
            {"id": str(item.get("id")), "name": item.get("name")}
            for item in lists
            if isinstance(item, dict) and item.get("id") is not None
        ]

    async def get_list(self, list_id: str) -> dict[str, Any] | None:
        """Consulta uma lista pelo ID, util para validar/exibir o nome da lista configurada."""
        if not self.settings.clickup_token:
            raise ClickUpServiceError("CLICKUP_TOKEN nao configurado.")

        url = f"{self.settings.clickup_base_url.rstrip('/')}/list/{list_id}"
        headers = {"Authorization": self.settings.clickup_token}

        try:
            async with httpx.AsyncClient(timeout=self.settings.request_timeout_seconds) as client:
                response = await client.get(url, headers=headers)
        except httpx.HTTPError:
            raise ClickUpServiceError("Erro de comunicacao ao consultar lista no ClickUp.") from None

        if response.status_code >= 400:
            return None

        try:
            return response.json()
        except ValueError:
            return None

    async def get_list_member_id_by_email(self, list_id: str, email: str) -> int | None:
        if not self.settings.clickup_token:
            raise ClickUpServiceError("CLICKUP_TOKEN nao configurado.")

        url = f"{self.settings.clickup_base_url.rstrip('/')}/list/{list_id}/member"
        headers = {"Authorization": self.settings.clickup_token}

        try:
            async with httpx.AsyncClient(timeout=self.settings.request_timeout_seconds) as client:
                response = await client.get(url, headers=headers)
        except httpx.HTTPError:
            return None

        if response.status_code >= 400:
            return None

        data = response.json()
        members = data.get("members") if isinstance(data, dict) else None
        if not isinstance(members, list):
            return None

        wanted_email = email.strip().lower()
        for member in members:
            if not isinstance(member, dict):
                continue
            user = member.get("user") if isinstance(member.get("user"), dict) else member
            user_email = str(user.get("email") or "").strip().lower()
            if user_email == wanted_email and user.get("id") is not None:
                try:
                    return int(user["id"])
                except (TypeError, ValueError):
                    return None

        return None
