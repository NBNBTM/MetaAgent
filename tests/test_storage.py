from meta_agent_app.storage import SQLiteStore


def test_sqlite_store_session_message_roundtrip(tmp_path):
    store = SQLiteStore(tmp_path / "metaagent.sqlite3")
    store.initialize()
    store.ensure_user("u1")

    session = store.create_session("u1", title="测试会话")
    store.add_message("u1", session["id"], "user", "你好")
    store.add_message("u1", session["id"], "assistant", "你好，有什么可以帮你？", name="元智能体")

    sessions = store.list_sessions("u1")
    messages = store.list_messages("u1", session["id"])

    assert sessions[0]["title"] == "测试会话"
    assert sessions[0]["message_count"] == 2
    assert [message["role"] for message in messages] == ["user", "assistant"]


def test_sqlite_store_resets_sessions(tmp_path):
    store = SQLiteStore(tmp_path / "metaagent.sqlite3")
    store.initialize()
    store.ensure_user("u1")
    session = store.create_session("u1")
    store.add_message("u1", session["id"], "user", "old")

    new_session = store.delete_all_sessions("u1")

    assert new_session["title"] == "新对话"
    assert store.list_messages("u1", new_session["id"]) == []
    assert len(store.list_sessions("u1")) == 1
