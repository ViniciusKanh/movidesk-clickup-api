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


def _section(title: str, body: str | Iterable[str]) -> str:
    if isinstance(body, str):
        content = body.strip()
    else:
        content = "\n".join(line for line in body if line.strip()).strip()

    if not content:
        return ""

    return f"""==============================
{title}
==============================
{content}"""


def _field_lines(pairs: Iterable[tuple[str, object]]) -> list[str]:
    lines = []
    for label, value in pairs:
        if _is_present(value):
            lines.append(f"{label}: {_clip(value, MAX_FIELD_VALUE_LENGTH)}")
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
        lines.append(f"- {name}: {_clip(value, MAX_FIELD_VALUE_LENGTH)}")

    return lines


def _bi_field_lines(ticket: MovideskTicket) -> list[str]:
    lines = []
    for name in HIGHLIGHTED_FIELD_NAMES:
        value = get_custom_field(ticket.custom_fields, name)
        if _is_present(value):
            clean_name = name.replace("[BI] ", "")
            lines.append(f"- {clean_name}: {_clip(value, MAX_FIELD_VALUE_LENGTH)}")
    return lines


def _action_type(value: object) -> str:
    text = _stringify(value)
    if text == "1":
        return "interna"
    if text == "2":
        return "publica"
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

    header = f"Acao {index}"
    if meta:
        header = f"{header} | {' | '.join(meta)}"

    description = _clip(action.description, MAX_ACTION_DESCRIPTION_LENGTH)
    if not description:
        description = "Sem descricao textual retornada pelo Movidesk."

    return f"{header}\n{description}"


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
        parts.append(f"Tipo de demanda: {_stringify(tipo)}.")
    if _is_present(dashboard):
        parts.append(f"Dashboard/projeto envolvido: {_stringify(dashboard)}.")
    if _is_present(area):
        parts.append(f"Área solicitante: {_stringify(area)}.")
    if _is_present(problema):
        parts.append(f"Problema informado: {_clip(problema, 450)}")
    if _is_present(resultado):
        parts.append(f"Resultado esperado: {_clip(resultado, 450)}")

    if not parts:
        return (
            "Demanda originada no Movidesk para análise e execução pelo time de BI. "
            "Validar o escopo diretamente no ticket antes de iniciar a implementação."
        )

    return "\n".join(parts)


def build_clickup_description(ticket: MovideskTicket) -> str:
    settings = get_settings()
    cf = ticket.custom_fields

    ticket_url = ""
    if settings.movidesk_ticket_url_template:
        ticket_url = settings.movidesk_ticket_url_template.format(ticket_id=ticket.id)

    origin_lines = _field_lines(
        (
            ("Ticket Movidesk", ticket.id),
            ("Link do ticket", ticket_url),
            ("Assunto", ticket.subject),
            ("Status Movidesk", ticket.status),
            ("Solicitante", ticket.requester_name),
            ("Responsável Movidesk", ticket.owner_name),
            ("Serviço", "GSI > BI > Melhoria/Projeto"),
        )
    )

    bi_lines = _bi_field_lines(ticket)
    extra_field_lines = _custom_field_lines(ticket)

    sections = [
        _section("RESUMO DA DEMANDA", _summary(ticket)),
        _section("ORIGEM", origin_lines),
        _section("DADOS DE BI PREENCHIDOS NO MOVIDESK", bi_lines),
        _section("OUTROS CAMPOS ADICIONAIS PREENCHIDOS", extra_field_lines),
        _section("ULTIMAS ACOES DO TICKET", _actions_section(ticket)),
        _section(
            "ESCOPO SUGERIDO",
            (
                "- Validar a necessidade registrada no ticket.",
                "- Avaliar fontes de dados e regras de negocio envolvidas.",
                "- Implementar a melhoria solicitada no dashboard, relatorio ou processo informado.",
                "- Testar o resultado com dados reais.",
                "- Solicitar validacao do solicitante.",
            ),
        ),
        _section(
            "CHECKLIST TECNICO",
            (
                "- [ ] Validar escopo da solicitacao no ticket Movidesk.",
                "- [ ] Validar fonte de dados envolvida.",
                "- [ ] Validar regra de negocio.",
                "- [ ] Identificar tabelas, campos e filtros necessarios.",
                "- [ ] Criar ou ajustar medidas/calculos.",
                "- [ ] Criar ou ajustar visualizacoes.",
                "- [ ] Validar integracao com filtros existentes.",
                "- [ ] Ajustar layout conforme padrao do dashboard.",
                "- [ ] Testar resultado com dados reais.",
                "- [ ] Solicitar validacao do solicitante.",
                "- [ ] Atualizar o ticket Movidesk com o andamento.",
                "- [ ] Encerrar tarefa no ClickUp apos validacao.",
            ),
        ),
    ]

    return "\n\n".join(section for section in sections if section.strip()) + "\n"
