# agents.md

## Project Overview

This repository provides a **small, opinionated conversation persistence library**.

It is **not** a vector DB or a RAG stack. Its only purpose is to:

- Create conversation IDs
- Append messages with metadata
- Persist data to a simple store
- Retrieve, list, export, and delete conversations

The package is intentionally minimal so hackathon teams can adopt it quickly.

---

## Directory Structure

From the perspective of this file (`agents.md`), the project root looks like:

```text
./
  agents.md
  CHANGELOG.md
  README.md
  pyproject.toml
  convosaver/
    __init__.py
    core.py
    models.py
    stores.py
    utils.py
  examples/
```

---

## Usage (Quick Test)

```python
from convosaver import ConvoSaver, MySQLConfig, MySQLStore

config = MySQLConfig(url="mysql+pymysql://convosaver:convosaverpass@127.0.0.1:3306/convosaver")
saver = ConvoSaver(MySQLStore(config))
conversation_id = saver.start()

saver.add_message(conversation_id, role="user", content="Hello")
saver.add_message(conversation_id, role="assistant", content="Hi!")

conversation = saver.get(conversation_id)
print(conversation.id, len(conversation.messages))
```

---

## Stores

- `MySQLStore` stores conversations and messages in MySQL using SQLAlchemy ORM.

All stores support soft delete, hard delete, listing, and trimming.

---

## Policy

`ConversationPolicy` can enforce:

- Maximum message count per conversation
- Maximum characters per message (strings only)
- Simple redaction with regex patterns

Policy is applied at write time in `ConvoSaver.add_message`.

---

## MySQL (Local Dev)

```bash
docker compose up -d
```

---

## RBAC Helpers (MySQLStore)

These helpers manage application-level access control:

- `ensure_user`, `ensure_role`, `assign_role`
- `grant_conversation_access`, `revoke_conversation_access`
- `check_conversation_access`, `authorize_or_raise`, `list_conversation_access`
- `require_access` (module helper)

---

## OpenAI Message Ingest

Use `add_openai_messages` to persist OpenAI-style message dicts without reshaping:

```python
messages = [
  {"role": "system", "content": "You are helpful."},
  {"role": "user", "content": "Hello"},
]
saver.add_openai_messages(conversation_id, messages)
```
