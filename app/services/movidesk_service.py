import html
from html.parser import HTMLParser
from typing import Any

import httpx

from app.config import get_settings
from app.schemas import MovideskTicket


class MovideskServiceError(Exception):
    pass


class MovideskService:
    """Cliente HTTP para consulta de tickets no Movidesk."""

    def __init__(self) -> None:
        self.settings = get_settings()

    async def get_ticket(self, ticket_id: int) -> MovideskTicket:
        if not self.settings.movidesk_token:
            raise MovideskServiceError("MOVIDESK_TOKEN nao configurado.")

        url = f"{self.settings.movidesk_base_url.rstrip('/')}/tickets"
        params = {
            "token": self.settings.movidesk_token,
            "id": ticket_id,
            "$expand": "customFieldValues($expand=items),clients,owner,actions($expand=createdBy)",
        }

        try:
            async with httpx.AsyncClient(timeout=self.settings.request_timeout_seconds) as client:
                response = await client.get(url, params=params)
        except httpx.HTTPError:
            raise MovideskServiceError("Erro de comunicacao ao consultar ticket no Movidesk.") from None

        if response.status_code >= 400:
            raise MovideskServiceError(f"Erro ao consultar ticket no Movidesk. HTTP {response.status_code}.")

        try:
            payload = response.json()
        except ValueError:
            raise MovideskServiceError("Resposta inesperada da API do Movidesk.") from None

        if isinstance(payload, list):
            if not payload:
                raise MovideskServiceError(f"Ticket {ticket_id} nao encontrado no Movidesk.")
            payload = payload[0]

        if not isinstance(payload, dict):
            raise MovideskServiceError("Resposta inesperada da API do Movidesk.")

        return self._parse_ticket(payload)

    def _parse_ticket(self, payload: dict[str, Any]) -> MovideskTicket:
        custom_fields = self._extract_custom_fields(payload.get("customFieldValues") or [])
        requester_name = self._extract_requester_name(payload.get("clients") or [])
        owner = payload.get("owner")
        owner_id = self._extract_owner_id(owner)
        owner_email = self._extract_owner_email(owner)
        owner_name = self._extract_owner_name(owner)
        actions = self._extract_actions(payload.get("actions") or [])

        ticket_id = payload.get("id") or payload.get("Id")
        subject = payload.get("subject") or payload.get("Subject") or ""

        if ticket_id is None:
            raise MovideskServiceError("Ticket retornado sem ID.")

        service_full = payload.get("serviceFull") or payload.get("service")

        return MovideskTicket(
            raw=payload,
            id=int(ticket_id),
            subject=str(subject).strip(),
            status=self._to_optional_str(payload.get("status")),
            service_first_level=self._to_optional_str(payload.get("serviceFirstLevel")),
            service_second_level=self._to_optional_str(payload.get("serviceSecondLevel")),
            service_third_level=self._to_optional_str(payload.get("serviceThirdLevel") or service_full),
            requester_name=requester_name,
            owner_id=owner_id,
            owner_email=owner_email,
            owner_name=owner_name,
            custom_fields=custom_fields,
            actions=actions,
        )

    @staticmethod
    def _extract_requester_name(clients: list[Any]) -> str | None:
        if not clients:
            return None
        first = clients[0]
        if not isinstance(first, dict):
            return None
        return MovideskService._to_optional_str(
            first.get("businessName")
            or first.get("personName")
            or first.get("name")
            or first.get("email")
            or first.get("id")
        )

    @staticmethod
    def _extract_owner_id(owner: Any) -> str | None:
        if not isinstance(owner, dict):
            return None
        return MovideskService._to_optional_str(owner.get("id") or owner.get("Id"))

    @staticmethod
    def _extract_owner_email(owner: Any) -> str | None:
        if not isinstance(owner, dict):
            return None
        emails = owner.get("emails")
        if isinstance(emails, list):
            for item in emails:
                if isinstance(item, dict) and item.get("email"):
                    return MovideskService._to_optional_str(item.get("email"))
        return MovideskService._to_optional_str(
            owner.get("email") or owner.get("Email") or owner.get("userName") or owner.get("accountEmail")
        )

    @staticmethod
    def _extract_owner_name(owner: Any) -> str | None:
        if not isinstance(owner, dict):
            return None
        return MovideskService._to_optional_str(
            owner.get("businessName")
            or owner.get("personName")
            or owner.get("name")
            or owner.get("email")
            or owner.get("id")
        )

    @staticmethod
    def _extract_actions(values: list[Any]) -> list[dict[str, Any]]:
        actions: list[dict[str, Any]] = []

        for item in values:
            if not isinstance(item, dict):
                continue

            created_by = item.get("createdBy") if isinstance(item.get("createdBy"), dict) else {}
            description = MovideskService._first_not_none(
                item.get("description"),
                item.get("htmlDescription"),
                item.get("text"),
                item.get("message"),
                item.get("justification"),
            )

            actions.append(
                {
                    "raw": item,
                    "id": item.get("id") or item.get("Id"),
                    "type": MovideskService._to_optional_str(item.get("type") or item.get("Type")),
                    "origin": MovideskService._to_optional_str(item.get("origin") or item.get("Origin")),
                    "status": MovideskService._to_optional_str(item.get("status") or item.get("Status")),
                    "created_date": MovideskService._to_optional_str(
                        item.get("createdDate") or item.get("createdAt") or item.get("date")
                    ),
                    "created_by_name": MovideskService._extract_person_name(created_by),
                    "description": MovideskService._clean_text(description),
                }
            )

        return actions

    @staticmethod
    def _extract_custom_fields(values: list[Any]) -> dict[str, Any]:
        result: dict[str, Any] = {}

        for item in values:
            if not isinstance(item, dict):
                continue

            custom_field = item.get("customField") if isinstance(item.get("customField"), dict) else {}
            field = item.get("field") if isinstance(item.get("field"), dict) else {}
            name = MovideskService._first_not_none(
                item.get("customFieldName"),
                item.get("name"),
                item.get("label"),
                item.get("fieldName"),
                custom_field.get("name"),
                custom_field.get("title"),
                field.get("name"),
                field.get("title"),
            )

            value: Any = MovideskService._first_not_none(
                item.get("value"),
                item.get("text"),
                item.get("customFieldValue"),
            )

            if value is None and isinstance(item.get("customFieldItem"), dict):
                value = item["customFieldItem"].get("customFieldItem") or item["customFieldItem"].get("name")

            if value is None and isinstance(item.get("items"), list):
                extracted_items = []
                for subitem in item["items"]:
                    if isinstance(subitem, dict):
                        extracted_items.append(
                            subitem.get("customFieldItem")
                            or subitem.get("name")
                            or subitem.get("value")
                            or str(subitem)
                        )
                    else:
                        extracted_items.append(subitem)
                value = ", ".join(str(v) for v in extracted_items if v is not None)

            if isinstance(value, list):
                value = ", ".join(str(v.get("name") if isinstance(v, dict) else v) for v in value)

            if name:
                result[str(name).strip()] = value

        return result

    @staticmethod
    def _first_not_none(*values: Any) -> Any:
        for value in values:
            if value is not None:
                return value
        return None

    @staticmethod
    def _extract_person_name(value: Any) -> str | None:
        if not isinstance(value, dict):
            return None
        return MovideskService._to_optional_str(
            value.get("businessName")
            or value.get("personName")
            or value.get("name")
            or value.get("userName")
            or value.get("email")
            or value.get("id")
        )

    @staticmethod
    def _clean_text(value: Any) -> str | None:
        if value is None:
            return None

        text = html.unescape(str(value)).replace("\xa0", " ")
        parser = _HTMLTextExtractor()
        parser.feed(text)
        cleaned = parser.text()
        return cleaned or str(value).strip() or None

    @staticmethod
    def _to_optional_str(value: Any) -> str | None:
        if value is None:
            return None
        if isinstance(value, (dict, list)):
            return str(value)
        text = str(value).strip()
        return text or None


class _HTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        if data.strip():
            self.parts.append(data.strip())

    def text(self) -> str:
        return " ".join(" ".join(self.parts).split())
