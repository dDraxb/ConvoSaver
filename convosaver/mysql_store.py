from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    String,
    Text,
    create_engine,
    func,
    select,
)
from sqlalchemy.orm import Session, declarative_base, relationship, sessionmaker

from .models import Conversation, Message
from .stores import BaseStore
from .utils import json_dumps, utc_now_iso

Base = declarative_base()


class ConversationRow(Base):
    __tablename__ = "conversations"

    id = Column(String(64), primary_key=True)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    metadata_json = Column(Text, nullable=True)

    messages = relationship("MessageRow", back_populates="conversation", cascade="all, delete-orphan")


class MessageRow(Base):
    __tablename__ = "messages"

    pk = Column(BigInteger, primary_key=True, autoincrement=True)
    id = Column(String(64), nullable=False)
    conversation_id = Column(String(64), ForeignKey("conversations.id"), nullable=False, index=True)
    role = Column(String(32), nullable=False)
    content_json = Column(Text, nullable=False)
    name = Column(String(128), nullable=True)
    tool_calls_json = Column(Text, nullable=True)
    tool_call_id = Column(String(128), nullable=True)
    meta_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False)

    conversation = relationship("ConversationRow", back_populates="messages")


class UserRow(Base):
    __tablename__ = "users"

    id = Column(String(64), primary_key=True)
    display_name = Column(String(128), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False)


class RoleRow(Base):
    __tablename__ = "roles"

    name = Column(String(64), primary_key=True)
    description = Column(String(256), nullable=True)


class UserRoleRow(Base):
    __tablename__ = "user_roles"

    pk = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(String(64), ForeignKey("users.id"), nullable=False, index=True)
    role_name = Column(String(64), ForeignKey("roles.name"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False)


class ConversationAccessRow(Base):
    __tablename__ = "conversation_access"

    pk = Column(BigInteger, primary_key=True, autoincrement=True)
    conversation_id = Column(String(64), ForeignKey("conversations.id"), nullable=False, index=True)
    subject_id = Column(String(64), ForeignKey("users.id"), nullable=False, index=True)
    role_name = Column(String(64), ForeignKey("roles.name"), nullable=False, index=True)
    granted_at = Column(DateTime(timezone=True), nullable=False)


@dataclass
class MySQLConfig:
    url: str
    pool_size: int = 5
    max_overflow: int = 10
    pool_recycle: int = 3600


class MySQLStore(BaseStore):
    def __init__(self, config: MySQLConfig) -> None:
        self._engine = create_engine(
            config.url,
            pool_size=config.pool_size,
            max_overflow=config.max_overflow,
            pool_recycle=config.pool_recycle,
            pool_pre_ping=True,
            future=True,
        )
        self._Session = sessionmaker(bind=self._engine, expire_on_commit=False, future=True)
        Base.metadata.create_all(self._engine)

    def create_conversation(self, conversation_id: str, *, created_at: str, updated_at: str, metadata: Dict[str, Any]) -> None:
        with self._session() as session:
            existing = session.get(ConversationRow, conversation_id)
            if existing is not None:
                return
            row = ConversationRow(
                id=conversation_id,
                created_at=self._parse_ts(created_at),
                updated_at=self._parse_ts(updated_at),
                deleted_at=None,
                metadata_json=json_dumps(metadata),
            )
            session.add(row)
            session.commit()

    def append_message(self, conversation_id: str, message: Message) -> None:
        with self._session() as session:
            convo = session.get(ConversationRow, conversation_id)
            if convo is None:
                convo = ConversationRow(
                    id=conversation_id,
                    created_at=self._parse_ts(message.created_at),
                    updated_at=self._parse_ts(message.created_at),
                    deleted_at=None,
                    metadata_json=json_dumps({}),
                )
                session.add(convo)
                session.flush()
            msg_row = MessageRow(
                id=message.id,
                conversation_id=conversation_id,
                role=message.role,
                content_json=json_dumps(message.content),
                name=message.name,
                tool_calls_json=json_dumps(message.tool_calls) if message.tool_calls is not None else None,
                tool_call_id=message.tool_call_id,
                meta_json=json_dumps(message.meta) if message.meta is not None else None,
                created_at=self._parse_ts(message.created_at),
            )
            session.add(msg_row)
            convo.updated_at = self._parse_ts(message.created_at)
            session.commit()

    def get_conversation(self, conversation_id: str, include_deleted: bool) -> Optional[Conversation]:
        with self._session() as session:
            convo = session.get(ConversationRow, conversation_id)
            if convo is None:
                return None
            if convo.deleted_at and not include_deleted:
                return None
            messages = (
                session.execute(
                    select(MessageRow).where(MessageRow.conversation_id == conversation_id).order_by(MessageRow.pk.asc())
                )
                .scalars()
                .all()
            )
            return Conversation(
                id=convo.id,
                created_at=convo.created_at.isoformat(),
                updated_at=convo.updated_at.isoformat(),
                deleted_at=convo.deleted_at.isoformat() if convo.deleted_at else None,
                metadata=self._json_load(convo.metadata_json),
                messages=[self._row_to_message(row) for row in messages],
            )

    def list_conversations(self, limit: int, offset: int, include_deleted: bool) -> List[Conversation]:
        with self._session() as session:
            query = select(ConversationRow)
            if not include_deleted:
                query = query.where(ConversationRow.deleted_at.is_(None))
            rows = (
                session.execute(query.order_by(ConversationRow.updated_at.desc()).limit(limit).offset(offset))
                .scalars()
                .all()
            )
            return [
                Conversation(
                    id=row.id,
                    created_at=row.created_at.isoformat(),
                    updated_at=row.updated_at.isoformat(),
                    deleted_at=row.deleted_at.isoformat() if row.deleted_at else None,
                    metadata=self._json_load(row.metadata_json),
                    messages=[],
                )
                for row in rows
            ]

    def soft_delete_conversation(self, conversation_id: str) -> None:
        with self._session() as session:
            convo = session.get(ConversationRow, conversation_id)
            if convo is None:
                return
            now = self._parse_ts(utc_now_iso())
            convo.deleted_at = now
            convo.updated_at = now
            session.commit()

    def hard_delete_conversation(self, conversation_id: str) -> None:
        with self._session() as session:
            session.execute(
                ConversationAccessRow.__table__.delete().where(
                    ConversationAccessRow.conversation_id == conversation_id
                )
            )
            convo = session.get(ConversationRow, conversation_id)
            if convo is None:
                return
            session.delete(convo)
            session.commit()

    def trim_conversation(self, conversation_id: str, keep_last: int) -> None:
        if keep_last <= 0:
            self.hard_delete_conversation(conversation_id)
            return
        with self._session() as session:
            subquery = (
                select(MessageRow.pk)
                .where(MessageRow.conversation_id == conversation_id)
                .order_by(MessageRow.pk.desc())
                .limit(keep_last)
                .subquery()
            )
            threshold = session.execute(select(func.min(subquery.c.pk))).scalar()
            if threshold is None:
                return
            session.execute(
                MessageRow.__table__.delete().where(
                    MessageRow.conversation_id == conversation_id, MessageRow.pk < threshold
                )
            )
            session.commit()

    def ensure_user(self, user_id: str, display_name: Optional[str] = None) -> None:
        with self._session() as session:
            user = session.get(UserRow, user_id)
            if user is None:
                user = UserRow(id=user_id, display_name=display_name, created_at=self._parse_ts(utc_now_iso()))
                session.add(user)
                session.commit()
                return
            if display_name is not None and user.display_name != display_name:
                user.display_name = display_name
                session.commit()

    def ensure_role(self, role_name: str, description: Optional[str] = None) -> None:
        with self._session() as session:
            role = session.get(RoleRow, role_name)
            if role is None:
                role = RoleRow(name=role_name, description=description)
                session.add(role)
                session.commit()
                return
            if description is not None and role.description != description:
                role.description = description
                session.commit()

    def assign_role(self, user_id: str, role_name: str) -> None:
        self.ensure_user(user_id)
        self.ensure_role(role_name)
        with self._session() as session:
            existing = session.execute(
                select(UserRoleRow).where(UserRoleRow.user_id == user_id, UserRoleRow.role_name == role_name)
            ).scalar_one_or_none()
            if existing is None:
                session.add(
                    UserRoleRow(
                        user_id=user_id,
                        role_name=role_name,
                        created_at=self._parse_ts(utc_now_iso()),
                    )
                )
                session.commit()

    def grant_conversation_access(self, conversation_id: str, user_id: str, role_name: str) -> None:
        self.ensure_user(user_id)
        self.ensure_role(role_name)
        with self._session() as session:
            existing = session.execute(
                select(ConversationAccessRow).where(
                    ConversationAccessRow.conversation_id == conversation_id,
                    ConversationAccessRow.subject_id == user_id,
                    ConversationAccessRow.role_name == role_name,
                )
            ).scalar_one_or_none()
            if existing is None:
                session.add(
                    ConversationAccessRow(
                        conversation_id=conversation_id,
                        subject_id=user_id,
                        role_name=role_name,
                        granted_at=self._parse_ts(utc_now_iso()),
                    )
                )
                session.commit()

    def revoke_conversation_access(self, conversation_id: str, user_id: str, role_name: Optional[str] = None) -> None:
        with self._session() as session:
            query = select(ConversationAccessRow).where(
                ConversationAccessRow.conversation_id == conversation_id,
                ConversationAccessRow.subject_id == user_id,
            )
            if role_name is not None:
                query = query.where(ConversationAccessRow.role_name == role_name)
            rows = session.execute(query).scalars().all()
            for row in rows:
                session.delete(row)
            if rows:
                session.commit()

    def check_conversation_access(self, conversation_id: str, user_id: str, roles: Optional[List[str]] = None) -> bool:
        with self._session() as session:
            query = select(ConversationAccessRow).where(
                ConversationAccessRow.conversation_id == conversation_id,
                ConversationAccessRow.subject_id == user_id,
            )
            if roles:
                query = query.where(ConversationAccessRow.role_name.in_(roles))
            row = session.execute(query.limit(1)).scalar_one_or_none()
            return row is not None

    def authorize_or_raise(self, conversation_id: str, user_id: str, roles: Optional[List[str]] = None) -> None:
        if not self.check_conversation_access(conversation_id, user_id, roles=roles):
            role_list = ", ".join(roles) if roles else "any"
            raise PermissionError(f"User '{user_id}' lacks required access ({role_list}).")

    def list_conversation_access(self, conversation_id: str) -> List[Dict[str, Any]]:
        with self._session() as session:
            rows = (
                session.execute(
                    select(ConversationAccessRow).where(ConversationAccessRow.conversation_id == conversation_id)
                )
                .scalars()
                .all()
            )
            return [
                {
                    "user_id": row.subject_id,
                    "role": row.role_name,
                    "granted_at": row.granted_at.isoformat(),
                }
                for row in rows
            ]

    def _session(self) -> Session:
        return self._Session()

    @staticmethod
    def _parse_ts(value: str):
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt

    @staticmethod
    def _json_load(value: Optional[str]) -> Dict[str, Any]:
        if not value:
            return {}
        return json.loads(value)

    @staticmethod
    def _row_to_message(row: MessageRow) -> Message:
        return Message(
            id=row.id,
            role=row.role,
            content=json.loads(row.content_json),
            name=row.name,
            tool_calls=json.loads(row.tool_calls_json) if row.tool_calls_json else None,
            tool_call_id=row.tool_call_id,
            meta=json.loads(row.meta_json) if row.meta_json else None,
            created_at=row.created_at.isoformat(),
        )
