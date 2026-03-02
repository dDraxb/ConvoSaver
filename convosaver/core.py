from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from .models import Conversation, ConversationPolicy, Message
from .stores import BaseStore
from .utils import (
    ensure_role,
    new_id,
    normalize_content,
    redact_text,
    truncate_text,
    utc_now_iso,
)


class ConvoSaver:
    def __init__(
        self,
        store: BaseStore,
        policy: Optional[ConversationPolicy] = None,
    ) -> None:
        self._store = store
        self._policy = policy or ConversationPolicy()

    def start(self, conversation_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> str:
        convo_id = conversation_id or new_id()
        now = utc_now_iso()
        self._store.create_conversation(convo_id, created_at=now, updated_at=now, metadata=metadata or {})
        return convo_id

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: Any,
        *,
        name: Optional[str] = None,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
        tool_call_id: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None,
        created_at: Optional[str] = None,
    ) -> Message:
        ensure_role(role)
        normalized = normalize_content(content)
        if isinstance(normalized, str):
            normalized = redact_text(normalized, self._policy.redact_patterns, self._policy.redact_replacement)
            normalized = truncate_text(normalized, self._policy.max_chars)
        msg = Message(
            id=new_id(),
            role=role,
            content=normalized,
            name=name,
            tool_calls=tool_calls,
            tool_call_id=tool_call_id,
            meta=meta,
            created_at=created_at or utc_now_iso(),
        )
        self._store.append_message(conversation_id, msg)
        if self._policy.max_messages is not None:
            self._store.trim_conversation(conversation_id, keep_last=self._policy.max_messages)
        return msg

    def add_messages(self, conversation_id: str, messages: Iterable[Message]) -> None:
        for message in messages:
            self._store.append_message(conversation_id, message)
        if self._policy.max_messages is not None:
            self._store.trim_conversation(conversation_id, keep_last=self._policy.max_messages)

    def add_openai_messages(self, conversation_id: str, messages: Iterable[Dict[str, Any]]) -> None:
        for raw in messages:
            self.add_message(
                conversation_id,
                role=raw.get("role", "user"),
                content=raw.get("content"),
                name=raw.get("name"),
                tool_calls=raw.get("tool_calls"),
                tool_call_id=raw.get("tool_call_id"),
                meta={k: v for k, v in raw.items() if k not in {"role", "content", "name", "tool_calls", "tool_call_id"}},
            )

    def get(self, conversation_id: str, include_deleted: bool = False) -> Optional[Conversation]:
        return self._store.get_conversation(conversation_id, include_deleted=include_deleted)

    def list(self, limit: int = 100, offset: int = 0, include_deleted: bool = False) -> List[Conversation]:
        return self._store.list_conversations(limit=limit, offset=offset, include_deleted=include_deleted)

    def delete(self, conversation_id: str, hard: bool = False) -> None:
        if hard:
            self._store.hard_delete_conversation(conversation_id)
        else:
            self._store.soft_delete_conversation(conversation_id)

    def export_json(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        convo = self._store.get_conversation(conversation_id, include_deleted=True)
        if convo is None:
            return None
        return {
            "id": convo.id,
            "created_at": convo.created_at,
            "updated_at": convo.updated_at,
            "deleted_at": convo.deleted_at,
            "metadata": convo.metadata,
            "messages": [
                {
                    "id": msg.id,
                    "role": msg.role,
                    "content": msg.content,
                    "name": msg.name,
                    "tool_calls": msg.tool_calls,
                    "tool_call_id": msg.tool_call_id,
                    "meta": msg.meta,
                    "created_at": msg.created_at,
                }
                for msg in convo.messages
            ],
        }
