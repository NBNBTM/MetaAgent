from __future__ import annotations

import importlib
import importlib.util
from pathlib import Path

import pandas as pd
import pytest
from fastmcp import FastMCP


SERVER_ROOT = Path(__file__).resolve().parents[1] / "mcp" / "server" / "mcp_server"


def load_restored_modules(monkeypatch):
    monkeypatch.syspath_prepend(str(SERVER_ROOT))
    assert importlib.util.find_spec("modules.internet_time") is not None
    assert importlib.util.find_spec("modules.data_visualization") is not None
    time_module = importlib.import_module("modules.internet_time")
    visualization_module = importlib.import_module("modules.data_visualization")
    return time_module.InternetTime, visualization_module.DataVisualizationModule


def test_fallback_config_matches_public_modules(monkeypatch, tmp_path):
    monkeypatch.syspath_prepend(str(SERVER_ROOT))
    config_manager = importlib.import_module("core.config_manager")

    config = config_manager.ConfigManager(tmp_path / "missing-config.json")

    assert set(config.get_modules_config()) == {
        "internet_time",
        "calculator",
        "data_analysis",
        "data_visualization",
    }


@pytest.mark.asyncio
async def test_restored_modules_register_all_public_tools(monkeypatch):
    InternetTime, DataVisualizationModule = load_restored_modules(monkeypatch)
    server = FastMCP("restored-tools")

    time_module = InternetTime()
    visualization_module = DataVisualizationModule()
    time_module.register(server)
    visualization_module.register(server)

    tool_names = {tool.name for tool in await server.list_tools()}
    assert tool_names == {
        "get_internet_time",
        "get_weekday",
        "shift_time",
        "check_visualization_data",
        "plot_line",
        "plot_bar",
        "plot_scatter",
        "plot_pie",
        "plot_box",
    }
    assert time_module.get_info()["author"] == "Weilin Shen"
    assert visualization_module.get_info()["author"] == "Chenyu Tian"
    assert "email" not in visualization_module.get_info()


@pytest.mark.asyncio
async def test_internet_time_uses_requested_url_and_parses_http_date(monkeypatch):
    InternetTime, _DataVisualizationModule = load_restored_modules(monkeypatch)
    requested = {}

    class Response:
        headers = {"Date": "Tue, 05 Aug 2025 06:30:00 GMT"}

        @staticmethod
        def raise_for_status():
            return None

    def fake_head(url, timeout, allow_redirects):
        requested.update(
            {"url": url, "timeout": timeout, "allow_redirects": allow_redirects}
        )
        return Response()

    internet_time = importlib.import_module("modules.internet_time.internet_time")
    monkeypatch.setattr(internet_time.requests, "head", fake_head)
    server = FastMCP("internet-time")
    InternetTime().register(server)

    result = await server.call_tool(
        "get_internet_time",
        {"server": "https://www.cloudflare.com"},
    )

    assert requested == {
        "url": "https://www.cloudflare.com",
        "timeout": 10,
        "allow_redirects": False,
    }
    assert result.structured_content == {
        "datetime": "2025-08-05 14:30:00",
        "weekday": "星期二",
        "timezone": "北京时间",
        "source": "HTTP Date header from https://www.cloudflare.com",
    }


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1:18899",
        "http://169.254.169.254/latest/meta-data/",
        "file:///etc/passwd",
        "https://example.com",
    ],
)
async def test_internet_time_rejects_unapproved_urls(monkeypatch, url):
    InternetTime, _DataVisualizationModule = load_restored_modules(monkeypatch)
    internet_time = importlib.import_module("modules.internet_time.internet_time")

    def unexpected_head(*_args, **_kwargs):
        raise AssertionError("A rejected URL must not trigger a network request")

    monkeypatch.setattr(internet_time.requests, "head", unexpected_head)
    server = FastMCP("internet-time")
    InternetTime().register(server)

    result = await server.call_tool("get_internet_time", {"server": url})

    assert result.structured_content == {
        "error": "Unsupported time server. Use one of the documented public sources."
    }


def test_visualization_service_generates_bar_chart(monkeypatch, tmp_path):
    _InternetTime, _DataVisualizationModule = load_restored_modules(monkeypatch)
    service_module = importlib.import_module(
        "modules.data_visualization.data_visualization_service"
    )
    source_path = tmp_path / "sample.csv"
    output_path = tmp_path / "bar.png"
    pd.DataFrame({"category": ["A", "B"], "value": [2, 5]}).to_csv(
        source_path,
        index=False,
    )

    result = service_module.DataVisualizationService().plot_bar(
        file_path=str(source_path),
        x_column="category",
        y_column="value",
        output_path=str(output_path),
    )

    assert result == {
        "status": "success",
        "message": "条形图绘制成功",
        "output_path": str(output_path),
    }
    assert output_path.is_file()
    assert output_path.stat().st_size > 0
