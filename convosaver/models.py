from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class Message:
    id: str
    role: str
    content: Any
    created_at: str
    name: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None


@dataclass
class Conversation:
    id: str
    created_at: str
    updated_at: str
    deleted_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    messages: List[Message] = field(default_factory=list)


@dataclass
class ConversationPolicy:
    max_messages: Optional[int] = None
    max_chars: Optional[int] = None
    redact_patterns: Optional[List[str]] = None
    redact_replacement: str = "[REDACTED]"
