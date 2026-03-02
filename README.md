# ConvoSaver

Lightweight conversation persistence for LLM apps using MySQL and SQLAlchemy ORM.

## What It Is

- A small Python package to persist chat messages and metadata.
- MySQL backend with ORM and optional RBAC helpers.
- A policy layer for trimming, truncation, and basic redaction.

## What It Is Not

- Not a vector store or RAG pipeline.
- Not a chat UI or server.
- Not a message broker.

## Quick Start (MySQL)

```bash
pip install -e .
```

```python
from convosaver import ConvoSaver, MySQLConfig, MySQLStore, ConversationPolicy

config = MySQLConfig(url="mysql+pymysql://convosaver:convosaverpass@127.0.0.1:3306/convosaver")
store = MySQLStore(config)
policy = ConversationPolicy(max_messages=50, max_chars=4000)
saver = ConvoSaver(store, policy=policy)

conversation_id = saver.start(metadata={"user_id": "alice"})

saver.add_message(conversation_id, role="user", content="Hello")
saver.add_message(conversation_id, role="assistant", content="Hi! How can I help?")

conversation = saver.get(conversation_id)
print(conversation.id, len(conversation.messages))
```

## Notes

- Messages are stored exactly as you send them. The package does not infer system prompts.
- `add_openai_messages` accepts OpenAI-style message dicts and persists them as-is.
- MySQLStore is the recommended backend for multi-user and role-based access patterns.

## Store Tradeoffs

- MySQLStore
- Full SQL with roles, grants, and concurrent writers.
- Requires a server and credentials.

## MySQL Docker (Local Dev)

```bash
docker compose up -d
```

## RBAC Helpers (MySQLStore)

These helpers provide **application-level access control** (not MySQL server roles):

```python
store.ensure_user("alice", display_name="Alice")
store.ensure_role("owner")
store.assign_role("alice", "owner")

store.grant_conversation_access(conversation_id, "alice", "owner")
allowed = store.check_conversation_access(conversation_id, "alice", roles=["owner", "editor"])
store.authorize_or_raise(conversation_id, "alice", roles=["owner", "editor"])
```

## Testing

```bash
CONVOSAVER_MYSQL_URL="mysql+pymysql://convosaver:convosaverpass@127.0.0.1:3306/convosaver" pytest
```

## Project Layout

```text
convosaver/
  __init__.py
  core.py
  models.py
  stores.py
  utils.py
examples/
README.md
agents.md
CHANGELOG.md
pyproject.toml
```
