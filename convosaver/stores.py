from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Iterable, List, Optional

from .models import Conversation, Message


class BaseStore(ABC):
    @abstractmethod
    def create_conversation(self, conversation_id: str, *, created_at: str, updated_at: str, metadata: Dict[str, Any]) -> None:
        raise NotImplementedError

    @abstractmethod
    def append_message(self, conversation_id: str, message: Message) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_conversation(self, conversation_id: str, include_deleted: bool) -> Optional[Conversation]:
        raise NotImplementedError

    @abstractmethod
    def list_conversations(self, limit: int, offset: int, include_deleted: bool) -> List[Conversation]:
        raise NotImplementedError

    @abstractmethod
    def soft_delete_conversation(self, conversation_id: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def hard_delete_conversation(self, conversation_id: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def trim_conversation(self, conversation_id: str, keep_last: int) -> None:
        raise NotImplementedError

