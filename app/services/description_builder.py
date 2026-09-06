from __future__ import annotations

import json
from typing import Iterable

from app.config import get_settings
from app.schemas import MovideskAction, MovideskTicket
from app.services.custom_fields import get_custom_field, normalize_label

MAX_FIELD_VALUE_LENGTH = 1200
MAX_ACTION_DESCRIPTION_LENGTH = 1800
MAX_ACTIONS_IN_DESCRIPTION = 8

CLICKUP_FIELD_LABELS = {
    normalize_label("[BI] ID ClickUp"),
    normalize_label("[BI] Link ClickUp"),
    normalize_label("[BI] Status integração ClickUp"),
    normalize_label("[BI] Mensagem erro integração"),
}

HIGHLIGHTED_FIELD_NAMES = (
    "[BI] Área solicitante",
    "[BI] Tipo de demanda",
    "[BI] Nome do dashboard/projeto",
    "[BI] Existe dashboard atual?",
    "[BI] Link do dashboard/relatório",
    "[BI] Prazo desejado",
    "[BI] Complexidade estimada",
    "[BI] Problema atual",
    "[BI] Resultado esperado",
)

# Emojis usados como icones de secao - dao escaneabilidade visual no ClickUp
# (que renderiza markdown_description como rich text), sem depender de HTML.
ICON_SUMMARY = "📋"
ICON_ORIGIN = "🎫"
ICON_BI = "🧭"
ICON_EXTRA = "🗂️"
ICON_ACTIONS = "🕘"
ICON_SCOPE = "🎯"

DIVIDER = "---"


def build_clickup_task_name(ticket: MovideskTicket) -> str:
    return f"[MOVI-{ticket.id}] {ticket.subject}"[:255]


def _is_present(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict)):
        return bool(value)
    return True


def _stringify(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return " ".join(value.split())
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False, default=str)
    return str(value).strip()


def _clip(value: object, limit: int) -> str:
    text = _stringify(value)
    if len(text) <= limit:
        return text
    return f"{text[:limit].rstrip()}...[truncado]"


def _heading(icon: str, title: str) -> str:
    return f"## {icon} {title}"


def _section(icon: str, title: str, body: str | Iterable[str]) -> str:
    if isinstance(body, str):
        content = body.strip()
    else:
        content = "\n".join(line for line in body if line.strip()).strip()

    if not content:
        return ""

    return f"{_heading(icon, title)}\n{content}"


def _bullet_lines(pairs: Iterable[tuple[str, object]]) -> list[str]:
    lines = []
    for label, value in pairs:
        if _is_present(value):
            lines.append(f"- **{label}:** {_clip(value, MAX_FIELD_VALUE_LENGTH)}")
    return lines


def _custom_field_lines(ticket: MovideskTicket) -> list[str]:
    lines = []
    highlighted = {normalize_label(name) for name in HIGHLIGHTED_FIELD_NAMES}

    for name, value in sorted(ticket.custom_fields.items(), key=lambda item: str(item[0]).lower()):
        normalized_name = normalize_label(name)
        if normalized_name in CLICKUP_FIELD_LABELS:
            continue
        if normalized_name in highlighted:
            continue
        if not _is_present(value):
            continue
        lines.append(f"- **{name}:** {_clip(value, MAX_FIELD_VALUE_LENGTH)}")

    return lines


def _bi_field_lines(ticket: MovideskTicket) -> list[str]:
    lines = []
    for name in HIGHLIGHTED_FIELD_NAMES:
        value = get_custom_field(ticket.custom_fields, name)
        if _is_present(value):
            clean_name = name.replace("[BI] ", "")
            lines.append(f"- **{clean_name}:** {_clip(value, MAX_FIELD_VALUE_LENGTH)}")
    return lines


def _action_type(value: object) -> str:
    text = _stringify(value)
    if text == "1":
        return "interna"
    if text == "2":
        return "pública"
    return text


def _build_action_line(action: MovideskAction, index: int) -> str:
    meta = []
    if _is_present(action.created_date):
        meta.append(_stringify(action.created_date))
    if _is_present(action.created_by_name):
        meta.append(_stringify(action.created_by_name))
    if _is_present(action.type):
        meta.append(f"tipo {_action_type(action.type)}")
    if _is_present(action.status):
        meta.append(f"status {_stringify(action.status)}")

    header = f"**Ação {index}**"
    if meta:
        header = f"{header} — {' · '.join(meta)}"

    description = _clip(action.description, MAX_ACTION_DESCRIPTION_LENGTH)
    if not description:
        description = "Sem descrição textual retornada pelo Movidesk."

    quoted = "\n".join(f"> {line}" if line.strip() else ">" for line in description.split("\n"))
    return f"{header}\n{quoted}"


def _actions_section(ticket: MovideskTicket) -> str:
    if not ticket.actions:
        return "Sem ações retornadas pelo Movidesk."

    selected_actions = ticket.actions[-MAX_ACTIONS_IN_DESCRIPTION:]
    return "\n\n".join(
        _build_action_line(action, index)
        for index, action in enumerate(selected_actions, start=1)
    )


def _summary(ticket: MovideskTicket) -> str:
    cf = ticket.custom_fields
    tipo = get_custom_field(cf, "[BI] Tipo de demanda")
    dashboard = get_custom_field(cf, "[BI] Nome do dashboard/projeto")
    area = get_custom_field(cf, "[BI] Área solicitante")
    problema = get_custom_field(cf, "[BI] Problema atual")
    resultado = get_custom_field(cf, "[BI] Resultado esperado")

    parts = []
    if _is_present(tipo):
        parts.append(f"**Tipo de demanda:** {_stringify(tipo)}")
    if _is_present(dashboard):
        parts.append(f"**Dashboard/projeto envolvido:** {_stringify(dashboard)}")
    if _is_present(area):
        parts.append(f"**Área solicitante:** {_stringify(area)}")
    if _is_present(problema):
        parts.append(f"**Problema informado:** {_clip(problema, 450)}")
    if _is_present(resultado):
        parts.append(f"**Resultado esperado:** {_clip(resultado, 450)}")

    if not parts:
        return (
            "Demanda originada no Movidesk para análise e execução pelo time de BI. "
            "Validar o escopo diretamente no ticket antes de iniciar a implementação."
        )

    return "\n".join(parts)


def build_clickup_description(ticket: MovideskTicket) -> str:
    settings = get_settings()

    # So aplica o template se ele realmente tiver o placeholder {ticket_id} - evita
    # mostrar um valor de configuracao incorreto (ex.: um GUID solto) como se fosse link.
    ticket_url = ""
    template = settings.movidesk_ticket_url_template or ""
    if "{ticket_id}" in template:
        ticket_url = template.format(ticket_id=ticket.id)

    origin_lines = _bullet_lines(
        (
            ("Ticket Movidesk", f"#{ticket.id}"),
            ("Link", f"[Abrir no Movidesk]({ticket_url})" if ticket_url else ""),
            ("Assunto", ticket.subject),
            ("Status", ticket.status),
            ("Categoria", ticket.category),
            ("Urgência", ticket.urgency),
            ("Tipo", ticket.ticket_type),
            ("Data de abertura", ticket.created_date),
            ("Solicitante", ticket.requester_name),
            ("Responsável Movidesk", ticket.owner_name),
            ("Equipe responsável", ticket.owner_team),
            ("Serviço", _service_display_name(ticket)),
            ("Tags", ", ".join(ticket.tags) if ticket.tags else ""),
        )
    )

    bi_lines = _bi_field_lines(ticket)
    extra_field_lines = _custom_field_lines(ticket)

    sections = [
        _section(ICON_SUMMARY, "Resumo da demanda", _summary(ticket)),
        _section(ICON_ORIGIN, "Origem", origin_lines),
        _section(ICON_BI, "Dados de BI preenchidos no Movidesk", bi_lines),
        _section(ICON_EXTRA, "Outros campos adicionais preenchidos", extra_field_lines),
        _section(ICON_ACTIONS, "Últimas ações do ticket", _actions_section(ticket)),
        _section(
            ICON_SCOPE,
            "Escopo sugerido",
            (
                "- Validar a necessidade registrada no ticket.",
                "- Avaliar fontes de dados e regras de negócio envolvidas.",
                "- Implementar a melhoria solicitada no dashboard, relatório ou processo informado.",
                "- Testar o resultado com dados reais.",
                "- Solicitar validação do solicitante.",
            ),
        ),
    ]

    non_empty = [section for section in sections if section.strip()]
    return f"\n\n{DIVIDER}\n\n".join(non_empty) + "\n"


def _service_display_name(ticket: MovideskTicket) -> str:
    settings = get_settings()
    if settings.required_service_display_name:
        return settings.required_service_display_name

    parts = [
        ticket.service_first_level,
        ticket.service_second_level,
        ticket.service_third_level,
    ]
    filled = [_stringify(part) for part in parts if _is_present(part)]
    return " > ".join(filled)
