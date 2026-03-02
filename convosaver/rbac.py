from __future__ import annotations

from typing import Iterable, Optional

from .mysql_store import MySQLStore


def require_access(
    store: MySQLStore,
    conversation_id: str,
    user_id: str,
    roles: Optional[Iterable[str]] = None,
) -> None:
    role_list = list(roles) if roles is not None else None
    store.authorize_or_raise(conversation_id, user_id, roles=role_list)
