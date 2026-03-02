import os
import uuid

import pytest

from convosaver import ConvoSaver, MySQLConfig, MySQLStore, require_access


MYSQL_URL = os.getenv("CONVOSAVER_MYSQL_URL")


@pytest.mark.skipif(not MYSQL_URL, reason="Set CONVOSAVER_MYSQL_URL to run MySQL tests")
def test_require_access_allows_when_granted():
    store = MySQLStore(MySQLConfig(url=MYSQL_URL))
    saver = ConvoSaver(store)

    conversation_id = saver.start()
    user_id = f"user_{uuid.uuid4().hex}"

    store.ensure_role("owner")
    store.grant_conversation_access(conversation_id, user_id, "owner")

    require_access(store, conversation_id, user_id, roles=["owner"])

    saver.delete(conversation_id, hard=True)


@pytest.mark.skipif(not MYSQL_URL, reason="Set CONVOSAVER_MYSQL_URL to run MySQL tests")
def test_require_access_denies_when_missing():
    store = MySQLStore(MySQLConfig(url=MYSQL_URL))
    saver = ConvoSaver(store)

    conversation_id = saver.start()
    user_id = f"user_{uuid.uuid4().hex}"

    with pytest.raises(PermissionError):
        require_access(store, conversation_id, user_id, roles=["owner"])

    saver.delete(conversation_id, hard=True)


@pytest.mark.skipif(not MYSQL_URL, reason="Set CONVOSAVER_MYSQL_URL to run MySQL tests")
def test_grant_and_revoke_access_flow():
    store = MySQLStore(MySQLConfig(url=MYSQL_URL))
    saver = ConvoSaver(store)

    conversation_id = saver.start()
    user_id = f"user_{uuid.uuid4().hex}"

    store.ensure_role("owner")
    store.grant_conversation_access(conversation_id, user_id, "owner")
    assert store.check_conversation_access(conversation_id, user_id, roles=["owner"]) is True

    store.revoke_conversation_access(conversation_id, user_id, role_name="owner")
    assert store.check_conversation_access(conversation_id, user_id, roles=["owner"]) is False

    saver.delete(conversation_id, hard=True)
