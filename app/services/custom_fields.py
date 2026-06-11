from __future__ import annotations

import unicodedata
from typing import Any


def _repair_mojibake(value: str) -> str:
    try:
        return value.encode("latin1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return value


def normalize_label(value: object) -> str:
    text = _repair_mojibake(str(value or "")).strip().lower()
    normalized = unicodedata.normalize("NFKD", text)
    without_accents = "".join(char for char in normalized if not unicodedata.combining(char))
    return " ".join(without_accents.split())


def get_custom_field(custom_fields: dict[str, Any], field_name: str, default: Any = None) -> Any:
    wanted = normalize_label(field_name)
    for key, value in custom_fields.items():
        if normalize_label(key) == wanted:
            return value
    return default
