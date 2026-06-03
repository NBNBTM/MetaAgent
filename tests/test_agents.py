from dataclasses import replace
from pathlib import Path

from meta_agent_app.agents import AgentService
from meta_agent_app.config import Settings
from meta_agent_app.storage import SQLiteStore


def build_service(tmp_path):
    settings = Settings.load(Path(__file__).resolve().parents[1])
    settings = replace(settings, data_dir=tmp_path, upload_dir=tmp_path / "uploads", database_path=tmp_path / "db.sqlite3")
    store = SQLiteStore(settings.database_path)
    store.initialize()
    store.ensure_user("u1")
    service = AgentService(settings, store)
    service.ensure_user_defaults("u1")
    return service, store


def test_agent_service_adds_common_tool_to_composed_agent(tmp_path):
    service, _store = build_service(tmp_path)

    agent = service.upsert_agent_from_payload("u1", {"name": "分析助手", "servers": ["数据分析", "数据绘图"]})

    assert agent["name"] == "分析助手"
    assert agent["servers"][0] == "通用工具"
    assert "数据分析" in agent["servers"]
    assert "数据绘图" in agent["servers"]


def test_agent_service_extracts_json_payload(tmp_path):
    service, _store = build_service(tmp_path)
    content = '先拆解任务。\n{"name": "计算助手", "servers": ["基础计算"]}'

    payload = service.extract_agent_payload(content)

    assert payload == {"name": "计算助手", "servers": ["基础计算"]}
