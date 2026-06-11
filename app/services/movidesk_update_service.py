from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import httpx

from app.config import get_settings
from app.schemas import MovideskTicket
from app.services.custom_fields import normalize_label

logger = logging.getLogger(__name__)


class MovideskUpdateServiceError(Exception):
    pass


@dataclass(frozen=True)
class MovideskClickUpUpdatePayload:
    ticket_id: int
    clickup_task_id: str
    clickup_task_url: str | None
    status_integracao: str
    mensagem: str | None = None


class MovideskUpdateService:
    """Atualiza campos adicionais do Movidesk na Fase 2, quando habilitado por ambiente."""

    TEXT_FIELDS = {
        "[BI] ID ClickUp": "clickup_task_id",
        "[BI] Link ClickUp": "clickup_task_url",
        "[BI] Mensagem erro integração": "mensagem",
    }
    SELECT_FIELDS = {
        "[BI] Status integração ClickUp": "status_integracao",
    }

    def __init__(self) -> None:
        self.settings = get_settings()

    async def update_clickup_fields(self, ticket: MovideskTicket, payload: MovideskClickUpUpdatePayload) -> bool:
        if not self.settings.enable_movidesk_update:
            logger.info(
                "Atualizacao automatica do Movidesk desativada. ticket_id=%s clickup_task_id=%s",
                payload.ticket_id,
                payload.clickup_task_id,
            )
            return False

        if not self.settings.movidesk_token:
            raise MovideskUpdateServiceError("MOVIDESK_TOKEN nao configurado para atualizar o Movidesk.")

        custom_fields = self._build_custom_field_values(ticket, payload)
        if not custom_fields:
            raise MovideskUpdateServiceError("Nenhum campo adicional de ClickUp encontrado no ticket Movidesk.")

        url = f"{self.settings.movidesk_base_url.rstrip('/')}/tickets"
        params = {"token": self.settings.movidesk_token, "id": payload.ticket_id}
        body = {"customFieldValues": custom_fields}

        try:
            async with httpx.AsyncClient(timeout=self.settings.request_timeout_seconds) as client:
                response = await client.patch(url, params=params, json=body)
        except httpx.HTTPError:
            raise MovideskUpdateServiceError("Erro de comunicacao ao atualizar campos ClickUp no Movidesk.") from None

        if response.status_code >= 400:
            raise MovideskUpdateServiceError(
                f"Erro ao atualizar campos ClickUp no Movidesk. HTTP {response.status_code}."
            )

        return True

    def _build_custom_field_values(
        self,
        ticket: MovideskTicket,
        payload: MovideskClickUpUpdatePayload,
    ) -> list[dict[str, Any]]:
        raw_values = ticket.raw.get("customFieldValues") if isinstance(ticket.raw, dict) else []
        if not isinstance(raw_values, list):
            return []

        target_text_fields = {normalize_label(name): attr for name, attr in self.TEXT_FIELDS.items()}
        target_select_fields = {normalize_label(name): attr for name, attr in self.SELECT_FIELDS.items()}
        result: list[dict[str, Any]] = []

        for raw_field in raw_values:
            if not isinstance(raw_field, dict):
                continue

            field = self._base_custom_field_payload(raw_field)
            if not field:
                continue

            normalized_name = normalize_label(self._extract_custom_field_name(raw_field))

            if normalized_name in target_text_fields:
                field["value"] = self._payload_value(payload, target_text_fields[normalized_name])
                field["items"] = []
            elif normalized_name in target_select_fields:
                value = self._payload_value(payload, target_select_fields[normalized_name])
                field["value"] = None
                field["items"] = [{"customFieldItem": value}] if value else []
            else:
                self._copy_existing_value(raw_field, field)

            result.append(field)

        return result

    @staticmethod
    def _payload_value(payload: MovideskClickUpUpdatePayload, attr: str) -> str:
        value = getattr(payload, attr)
        if value is None:
            return ""
        return str(value).strip()

    @staticmethod
    def _base_custom_field_payload(raw_field: dict[str, Any]) -> dict[str, Any] | None:
        custom_field_id = raw_field.get("customFieldId") or raw_field.get("CustomFieldId")
        rule_id = raw_field.get("customFieldRuleId") or raw_field.get("CustomFieldRuleId")
        line = raw_field.get("line") or raw_field.get("Line") or 1

        if custom_field_id is None or rule_id is None:
            return None

        return {
            "customFieldId": custom_field_id,
            "customFieldRuleId": rule_id,
            "line": line,
        }

    @staticmethod
    def _copy_existing_value(raw_field: dict[str, Any], field: dict[str, Any]) -> None:
        if "value" in raw_field:
            field["value"] = raw_field.get("value")
        elif "Value" in raw_field:
            field["value"] = raw_field.get("Value")

        items = raw_field.get("items") or raw_field.get("Items")
        if isinstance(items, list):
            field["items"] = [MovideskUpdateService._simplify_item(item) for item in items if isinstance(item, dict)]
        else:
            field["items"] = []

    @staticmethod
    def _simplify_item(item: dict[str, Any]) -> dict[str, Any]:
        allowed_keys = (
            "customFieldItem",
            "CustomFieldItem",
            "personId",
            "PersonId",
            "clientId",
            "ClientId",
            "team",
            "Team",
            "storageFileGuid",
            "StorageFileGuid",
        )
        return {key: item[key] for key in allowed_keys if key in item and item[key] is not None}

    @staticmethod
    def _extract_custom_field_name(raw_field: dict[str, Any]) -> str:
        custom_field = raw_field.get("customField") if isinstance(raw_field.get("customField"), dict) else {}
        field = raw_field.get("field") if isinstance(raw_field.get("field"), dict) else {}
        return str(
            raw_field.get("customFieldName")
            or raw_field.get("name")
            or raw_field.get("label")
            or raw_field.get("fieldName")
            or custom_field.get("name")
            or custom_field.get("title")
            or field.get("name")
            or field.get("title")
            or ""
        ).strip()
