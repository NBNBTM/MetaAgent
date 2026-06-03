from dataclasses import replace
from io import BytesIO
from pathlib import Path

import pytest
from quart.datastructures import FileStorage

from meta_agent_app import create_app
from meta_agent_app.config import Settings


def build_app(tmp_path):
    settings = Settings.load(Path(__file__).resolve().parents[1])
    settings = replace(
        settings,
        data_dir=tmp_path,
        upload_dir=tmp_path / "uploads",
        database_path=tmp_path / "db.sqlite3",
        openai_api_key="",
    )
    return create_app(settings)


@pytest.mark.asyncio
async def test_bootstrap_creates_user_session_and_default_agent(tmp_path):
    app = build_app(tmp_path)
    client = app.test_client()

    response = await client.get("/api/bootstrap")
    data = await response.get_json()

    assert response.status_code == 200
    assert data["session"]["title"] == "新对话"
    assert data["agents"][0]["name"] == "元智能体"


@pytest.mark.asyncio
async def test_meta_stream_uses_local_fallback_without_api_key(tmp_path):
    app = build_app(tmp_path)
    client = app.test_client()
    bootstrap = await client.get("/api/bootstrap")
    session_id = (await bootstrap.get_json())["session"]["id"]

    response = await client.get(
        "/stream",
        query_string={
            "session_id": session_id,
            "selected_agent": "元智能体",
            "userinput": "帮我计算一组数字",
        },
    )
    body = (await response.get_data()).decode("utf-8")

    assert response.status_code == 200
    assert "OPENAI_API_KEY" in body
    assert "agent_updated" in body


@pytest.mark.asyncio
async def test_upload_rejects_unsupported_extension(tmp_path):
    app = build_app(tmp_path)
    client = app.test_client()

    response = await client.post(
        "/api/upload",
        files={"file": FileStorage(stream=BytesIO(b"bad"), filename="secret.exe", name="file")},
    )
    data = await response.get_json()

    assert response.status_code == 400
    assert data["success"] is False
