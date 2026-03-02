from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Iterable, Optional


ALLOWED_ROLES = {"system", "user", "assistant", "tool", "developer", "function"}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def new_id() -> str:
    return uuid.uuid4().hex


def ensure_role(role: str) -> str:
    if role not in ALLOWED_ROLES:
        raise ValueError(f"Unsupported role: {role}")
    return role


def normalize_content(content: Any) -> Any:
    if isinstance(content, (str, int, float, bool)) or content is None:
        return content
    try:
        json.dumps(content)
        return content
    except TypeError as exc:
        raise ValueError("Content must be JSON-serializable") from exc


def truncate_text(value: str, max_chars: Optional[int]) -> str:
    if max_chars is None:
        return value
    if max_chars <= 0:
        return ""
    if len(value) <= max_chars:
        return value
    if max_chars <= 3:
        return value[:max_chars]
    return value[: max_chars - 3] + "..."


def redact_text(value: str, patterns: Optional[Iterable[str]], replacement: str) -> str:
    if not patterns:
        return value
    redacted = value
    for pattern in patterns:
        redacted = re.sub(pattern, replacement, redacted)
    return redacted


def json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"), default=str)
