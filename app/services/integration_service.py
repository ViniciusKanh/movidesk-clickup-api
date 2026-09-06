from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import ClickUpMonthlyList, IntegrationLog
from app.schemas import MovideskTicket, WebhookResponse
from app.services.clickup_service import ClickUpService, ClickUpServiceError
from app.services.custom_fields import get_custom_field, normalize_label
from app.services.description_builder import build_clickup_description, build_clickup_task_name
from app.services.movidesk_service import MovideskService, MovideskServiceError
from app.services.movidesk_update_service import (
    MovideskClickUpUpdatePayload,
    MovideskUpdateService,
    MovideskUpdateServiceError,
)

logger = logging.getLogger(__name__)

STATUS_RECEIVED = "RECEIVED"
STATUS_CREATED = "CREATED_SUCCESSFULLY"
STATUS_DUPLICATE = "IGNORED_DUPLICATE"
STATUS_IGNORED_VALIDATION = "IGNORED_VALIDATION"
STATUS_IGNORED_OWNER = "IGNORED_OWNER"
STATUS_ERROR_MOVIDESK = "ERROR_MOVIDESK"
STATUS_ERROR_CLICKUP = "ERROR_CLICKUP"
STATUS_ERROR_VALIDATION = "ERROR_VALIDATION"
STATUS_ERROR_INTERNAL = "ERROR_INTERNAL"

CLOSED_STATUSES = {
    "resolvido",
    "fechado",
    "cancelado",
    "aguardando informacao",
}

SENSITIVE_FIELD_MARKERS = (
    "authorization",
    "password",
    "senha",
    "secret",
    "token",
    "api_key",
    "apikey",
)


@dataclass(frozen=True)
class ClickUpDestination:
    clickup_list_id: str
    clickup_list_name: str


class IntegrationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.settings = get_settings()
        self.movidesk = MovideskService()
        self.clickup = ClickUpService()
        self.movidesk_update = MovideskUpdateService()

    async def process_movidesk_webhook(self, payload: dict[str, Any]) -> WebhookResponse:
        ticket_id = self.extract_ticket_id(payload)
        if not ticket_id:
            self._log(
                None,
                None,
                payload,
                None,
                None,
                STATUS_ERROR_VALIDATION,
                "ID do ticket nao encontrado no payload.",
            )
            return WebhookResponse(success=False, message="ID do ticket nao encontrado no payload.")

        self._log(ticket_id, None, payload, None, None, STATUS_RECEIVED, "Webhook recebido.")

        existing_log = self._get_success_log(ticket_id)
        if existing_log:
            await self._update_movidesk_from_existing_log(ticket_id, payload, existing_log)
            self._log(ticket_id, None, payload, None, None, STATUS_DUPLICATE, "Ticket ja integrado anteriormente.")
            return WebhookResponse(
                success=True,
                message="Ticket já integrado anteriormente. Nenhuma nova tarefa foi criada.",
                ticket_id=ticket_id,
            )

        try:
            ticket = await self.movidesk.get_ticket(ticket_id)
        except MovideskServiceError as exc:
            self._log(ticket_id, None, payload, None, None, STATUS_ERROR_MOVIDESK, str(exc))
            return WebhookResponse(success=False, message=str(exc), ticket_id=ticket_id)
        except Exception:  # noqa: BLE001
            logger.exception("Erro inesperado ao consultar ou mapear ticket no Movidesk")
            message = "Erro ao consultar ou interpretar ticket no Movidesk."
            self._log(ticket_id, None, payload, None, None, STATUS_ERROR_MOVIDESK, message)
            return WebhookResponse(success=False, message=message, ticket_id=ticket_id)

        if not self._owner_matches(ticket):
            message = "Ticket ignorado: responsavel atual nao e o usuario configurado para a integracao."
            self._log(ticket_id, ticket.subject, payload, None, None, STATUS_IGNORED_OWNER, message)
            return WebhookResponse(success=False, message=message, ticket_id=ticket_id)

        validation_error = self._validate_ticket(ticket)
        if validation_error:
            self._log(ticket_id, ticket.subject, payload, None, None, STATUS_IGNORED_VALIDATION, validation_error)
            return WebhookResponse(success=False, message=validation_error, ticket_id=ticket_id)

        active_list = self._get_active_clickup_list()
        if not active_list:
            message = "Nenhuma lista mensal ativa do ClickUp cadastrada."
            self._log(ticket_id, ticket.subject, payload, None, None, STATUS_ERROR_VALIDATION, message)
            return WebhookResponse(success=False, message=message, ticket_id=ticket_id)

        try:
            assignee_ids = await self._resolve_clickup_assignee_ids(active_list.clickup_list_id)
            task = await self.clickup.create_task(
                list_id=active_list.clickup_list_id,
                name=build_clickup_task_name(ticket),
                description=build_clickup_description(ticket),
                tags=["movidesk", "bi", "melhoria-projeto"],
                assignee_ids=assignee_ids,
                status=self.settings.clickup_task_status or None,
            )
        except ClickUpServiceError as exc:
            self._log(ticket_id, ticket.subject, payload, None, None, STATUS_ERROR_CLICKUP, str(exc))
            return WebhookResponse(success=False, message=str(exc), ticket_id=ticket_id)
        except Exception:  # noqa: BLE001
            logger.exception("Erro interno ao criar tarefa no ClickUp")
            self._log(
                ticket_id,
                ticket.subject,
                payload,
                None,
                None,
                STATUS_ERROR_INTERNAL,
                "Erro interno ao criar tarefa no ClickUp.",
            )
            return WebhookResponse(success=False, message="Erro interno ao criar tarefa no ClickUp.", ticket_id=ticket_id)

        self._log(
            ticket_id=ticket_id,
            ticket_subject=ticket.subject,
            payload=payload,
            clickup_task_id=task["id"],
            clickup_task_url=task.get("url"),
            status=STATUS_CREATED,
            message="Tarefa criada no ClickUp com sucesso.",
        )

        await self._update_movidesk_after_success(ticket, payload, task["id"], task.get("url"))

        return WebhookResponse(
            success=True,
            message="Tarefa criada no ClickUp com sucesso.",
            ticket_id=ticket_id,
            clickup_task_id=task["id"],
            clickup_task_url=task.get("url"),
        )

    async def diagnose_ticket(self, ticket_id: int) -> dict[str, Any]:
        """Diagnostico somente leitura de elegibilidade de um ticket.

        Reutiliza exatamente as mesmas checagens do fluxo real (_get_success_log,
        _owner_matches, _validate_ticket, _get_active_clickup_list) para o resultado
        ser sempre coerente com o que aconteceria em um webhook real, mas NUNCA cria
        tarefa no ClickUp nem altera nada no Movidesk (apenas 1 GET no Movidesk).
        """
        existing_log = self._get_success_log(ticket_id)

        try:
            ticket = await self.movidesk.get_ticket(ticket_id)
        except MovideskServiceError as exc:
            return {"ticket_id": ticket_id, "found": False, "error": str(exc), "verdict": str(exc)}

        required_id = (self.settings.movidesk_required_owner_id or "").strip()
        required_email = (self.settings.movidesk_required_owner_email or "").strip()
        required_name = (self.settings.movidesk_required_owner_name or "").strip()
        if required_id:
            owner_rule, owner_required_value = "id", required_id
        elif required_email:
            owner_rule, owner_required_value = "email", required_email
        elif required_name:
            owner_rule, owner_required_value = "nome", required_name
        else:
            owner_rule, owner_required_value = "nenhuma (nao bloqueia)", None

        owner_matches = self._owner_matches(ticket)
        validation_error = self._validate_ticket(ticket)
        active_list = self._get_active_clickup_list()

        would_create = bool(
            not existing_log and owner_matches and not validation_error and active_list is not None
        )

        if existing_log:
            verdict = "Ja integrado anteriormente: um novo webhook seria idempotente (nao criaria nova tarefa)."
        elif not owner_matches:
            verdict = "NAO criaria tarefa: o responsavel atual do ticket nao corresponde a regra configurada."
        elif validation_error:
            verdict = f"NAO criaria tarefa: {validation_error}"
        elif not active_list:
            verdict = "NAO criaria tarefa: nenhuma lista do ClickUp ativa/configurada."
        else:
            verdict = "Criaria uma tarefa no ClickUp agora, se um webhook chegasse para este ticket."

        return {
            "ticket_id": ticket.id,
            "found": True,
            "subject": ticket.subject,
            "status": ticket.status,
            "already_integrated": bool(existing_log),
            "existing_clickup_task_id": existing_log.clickup_task_id if existing_log else None,
            "existing_clickup_task_url": existing_log.clickup_task_url if existing_log else None,
            "owner_rule": owner_rule,
            "owner_required_value": owner_required_value,
            "owner_id": ticket.owner_id,
            "owner_email": ticket.owner_email,
            "owner_name": ticket.owner_name,
            "owner_matches": owner_matches,
            "service_first_level": ticket.service_first_level,
            "service_second_level": ticket.service_second_level,
            "service_third_level": ticket.service_third_level,
            "custom_field_criar_tarefa": get_custom_field(ticket.custom_fields, "[BI] Criar tarefa no ClickUp?"),
            "custom_field_link_clickup": get_custom_field(ticket.custom_fields, "[BI] Link ClickUp"),
            "validation_error": validation_error,
            "active_clickup_list_id": active_list.clickup_list_id if active_list else None,
            "active_clickup_list_name": active_list.clickup_list_name if active_list else None,
            "would_create_task": would_create,
            "verdict": verdict,
        }

    @staticmethod
    def extract_ticket_id(payload: dict[str, Any]) -> int | None:
        possible_keys = (
            "Id",
            "id",
            "TicketId",
            "ticketId",
            "ticket_id",
            "TicketID",
            "Ticket.Id",
            "ticket.id",
            "number",
            "Number",
            "numero",
            "Número",
            "número",
            "ticketNumber",
            "TicketNumber",
            "ticket_number",
        )
        for key in possible_keys:
            value = payload.get(key)
            if value is None:
                continue
            parsed = IntegrationService._parse_int(value)
            if parsed is not None:
                return parsed

        for path in (("Ticket", "Id"), ("Ticket", "id"), ("ticket", "Id"), ("ticket", "id")):
            value = IntegrationService._get_nested_value(payload, path)
            parsed = IntegrationService._parse_int(value)
            if parsed is not None:
                return parsed

        for value in payload.values():
            if isinstance(value, dict):
                nested = IntegrationService.extract_ticket_id(value)
                if nested:
                    return nested
        return None

    @staticmethod
    def _parse_int(value: Any) -> int | None:
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _get_nested_value(payload: dict[str, Any], path: tuple[str, ...]) -> Any:
        current: Any = payload
        for key in path:
            if not isinstance(current, dict):
                return None
            current = current.get(key)
        return current

    def _get_success_log(self, ticket_id: int) -> IntegrationLog | None:
        return (
            self.db.query(IntegrationLog)
            .filter(IntegrationLog.ticket_id == ticket_id, IntegrationLog.status == STATUS_CREATED)
            .order_by(IntegrationLog.created_at.desc())
            .first()
        )

    def _get_active_clickup_list(self) -> ClickUpMonthlyList | ClickUpDestination | None:
        active_list = self.db.query(ClickUpMonthlyList).filter(ClickUpMonthlyList.active.is_(True)).first()
        if active_list:
            return active_list

        if self.settings.clickup_default_list_id:
            return ClickUpDestination(
                clickup_list_id=self.settings.clickup_default_list_id,
                clickup_list_name=self.settings.clickup_default_list_name or "Default ClickUp list",
            )

        return None

    def _validate_ticket(self, ticket: MovideskTicket) -> str | None:
        if not ticket.id:
            return "Ticket sem ID."

        if not ticket.subject:
            return "Ticket sem assunto."

        if not self._service_matches(ticket):
            return f"Ticket nao pertence ao servico esperado: {self._required_service_display_name()}."

        normalized_status = normalize_label(ticket.status)
        if normalized_status in CLOSED_STATUSES:
            return f"Ticket com status bloqueado para integracao: {ticket.status}."

        criar_clickup = get_custom_field(ticket.custom_fields, "[BI] Criar tarefa no ClickUp?")
        if criar_clickup is not None and normalize_label(criar_clickup) not in {"sim", "s", "yes", "true", "1"}:
            return "Campo [BI] Criar tarefa no ClickUp? diferente de Sim."

        link_clickup = get_custom_field(ticket.custom_fields, "[BI] Link ClickUp")
        if link_clickup is not None and str(link_clickup).strip():
            return "Ticket ja possui Link ClickUp preenchido."

        return None

    async def _resolve_clickup_assignee_ids(self, list_id: str) -> list[int]:
        configured_ids = self._parse_assignee_ids(self.settings.clickup_assignee_ids)
        if configured_ids:
            return configured_ids

        wanted_email = (self.settings.clickup_assignee_email or "").strip().lower()
        if wanted_email:
            member_id = await self.clickup.get_list_member_id_by_email(list_id, wanted_email)
            if member_id:
                return [member_id]

        if self.settings.clickup_assign_authorized_user:
            user = await self.clickup.get_authorized_user()
            if user and user.get("id") is not None:
                user_email = str(user.get("email") or "").strip().lower()
                if not wanted_email or user_email == wanted_email:
                    try:
                        return [int(user["id"])]
                    except (TypeError, ValueError):
                        return []

        return []

    async def _update_movidesk_from_existing_log(
        self,
        ticket_id: int,
        payload: dict[str, Any],
        log: IntegrationLog,
    ) -> None:
        if not self.settings.enable_movidesk_update or not log.clickup_task_id:
            return

        try:
            ticket = await self.movidesk.get_ticket(ticket_id)
        except Exception:  # noqa: BLE001
            logger.exception("Erro ao consultar ticket duplicado para atualizacao no Movidesk")
            self._log(
                ticket_id,
                None,
                payload,
                log.clickup_task_id,
                log.clickup_task_url,
                STATUS_ERROR_MOVIDESK,
                "Ticket ja integrado, mas nao foi possivel consultar o Movidesk para atualizar campos.",
            )
            return

        await self._update_movidesk_after_success(ticket, payload, log.clickup_task_id, log.clickup_task_url)

    async def _update_movidesk_after_success(
        self,
        ticket: MovideskTicket,
        payload: dict[str, Any],
        clickup_task_id: str,
        clickup_task_url: str | None,
    ) -> None:
        if not self.settings.enable_movidesk_update:
            return

        update_payload = MovideskClickUpUpdatePayload(
            ticket_id=ticket.id,
            clickup_task_id=clickup_task_id,
            clickup_task_url=clickup_task_url,
            status_integracao=self.settings.movidesk_success_status_value,
            mensagem="",
        )

        try:
            updated = await self.movidesk_update.update_clickup_fields(ticket, update_payload)
        except MovideskUpdateServiceError as exc:
            self._log(
                ticket.id,
                ticket.subject,
                payload,
                clickup_task_id,
                clickup_task_url,
                STATUS_ERROR_MOVIDESK,
                str(exc),
            )
            return

        if updated:
            self._log(
                ticket.id,
                ticket.subject,
                payload,
                clickup_task_id,
                clickup_task_url,
                STATUS_CREATED,
                "Tarefa criada no ClickUp e campos do Movidesk atualizados com sucesso.",
            )

    @staticmethod
    def _parse_assignee_ids(value: str) -> list[int]:
        ids: list[int] = []
        for item in (value or "").split(","):
            item = item.strip()
            if not item:
                continue
            try:
                ids.append(int(item))
            except ValueError:
                continue
        return ids

    def _owner_matches(self, ticket: MovideskTicket) -> bool:
        """Valida se o responsavel atual do ticket e o usuario configurado para a integracao.

        Ordem de preferencia: ID do agente > e-mail > nome (fallback).
        Usa apenas o primeiro criterio configurado, evitando comparacoes ambiguas.
        Se nenhum criterio estiver configurado, preserva o comportamento anterior (nao bloqueia).
        """
        required_id = (self.settings.movidesk_required_owner_id or "").strip()
        if required_id:
            return normalize_label(ticket.owner_id) == normalize_label(required_id)

        required_email = (self.settings.movidesk_required_owner_email or "").strip()
        if required_email:
            ticket_email = (ticket.owner_email or "").strip().lower()
            return ticket_email == required_email.strip().lower()

        required_name = (self.settings.movidesk_required_owner_name or "").strip()
        if required_name:
            return normalize_label(ticket.owner_name) == normalize_label(required_name)

        return True

    @staticmethod
    def _service_matches(ticket: MovideskTicket) -> bool:
        settings = get_settings()
        required_values = [
            settings.required_service_first_level,
            settings.required_service_second_level,
            settings.required_service_third_level,
        ]
        required_parts = [normalize_label(value) for value in required_values if value]
        if not required_parts:
            return True

        service_values = [
            ticket.service_first_level,
            ticket.service_second_level,
            ticket.service_third_level,
        ]
        normalized_parts = [normalize_label(value) for value in service_values if value]
        joined = " > ".join(normalized_parts)

        return all(required in normalized_parts or required in joined for required in required_parts)

    def _required_service_display_name(self) -> str:
        if self.settings.required_service_display_name:
            return self.settings.required_service_display_name

        parts = [
            self.settings.required_service_first_level,
            self.settings.required_service_second_level,
            self.settings.required_service_third_level,
        ]
        configured = [part for part in parts if part]
        return " > ".join(configured) if configured else "qualquer servico"

    def _log(
        self,
        ticket_id: int | None,
        ticket_subject: str | None,
        payload: dict[str, Any],
        clickup_task_id: str | None,
        clickup_task_url: str | None,
        status: str,
        message: str,
    ) -> None:
        row = IntegrationLog(
            ticket_id=ticket_id,
            ticket_subject=ticket_subject,
            movidesk_payload=self._safe_json_payload(payload),
            clickup_task_id=clickup_task_id,
            clickup_task_url=clickup_task_url,
            status=status,
            message=message,
        )
        self.db.add(row)
        self.db.commit()

    @staticmethod
    def _safe_json_payload(payload: dict[str, Any]) -> str:
        sanitized = IntegrationService._sanitize_value(payload)
        return json.dumps(sanitized, ensure_ascii=False, default=str)

    @staticmethod
    def _sanitize_value(value: Any) -> Any:
        if isinstance(value, dict):
            safe: dict[str, Any] = {}
            for key, item in value.items():
                normalized_key = normalize_label(key)
                if any(marker in normalized_key for marker in SENSITIVE_FIELD_MARKERS):
                    safe[str(key)] = "[REDACTED]"
                else:
                    safe[str(key)] = IntegrationService._sanitize_value(item)
            return safe

        if isinstance(value, list):
            return [IntegrationService._sanitize_value(item) for item in value[:20]]

        if isinstance(value, str) and len(value) > 500:
            return f"{value[:500]}...[TRUNCATED]"

        return value
