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


def test_agent_service_restores_all_public_capability_groups(tmp_path):
    service, _store = build_service(tmp_path)

    assert set(service.catalog_by_name) == {"通用工具", "基础计算", "数据分析", "数据绘图"}


def test_agent_service_adds_common_tool_and_filters_unknown_servers(tmp_path):
    service, _store = build_service(tmp_path)

    servers = service.normalize_servers(["数据分析", "数据绘图", "不存在的工具"])

    assert servers == ["通用工具", "数据分析", "数据绘图"]


def test_agent_service_routes_time_and_visualization_requests(tmp_path):
    service, _store = build_service(tmp_path)

    time_agent = service.infer_agent_payload("今天是星期几？")
    chart_agent = service.infer_agent_payload("分析 CSV 数据并画柱状图")

    assert time_agent == {"name": "通用助手", "servers": ["通用工具"]}
    assert chart_agent == {
        "name": "数据分析数据绘图助手",
        "servers": ["通用工具", "数据分析", "数据绘图"],
    }


def test_agent_service_extracts_json_payload(tmp_path):
    service, _store = build_service(tmp_path)
    content = '先拆解任务。\n{"name": "计算助手", "servers": ["基础计算"]}'

    payload = service.extract_agent_payload(content)

    assert payload == {"name": "计算助手", "servers": ["基础计算"]}
