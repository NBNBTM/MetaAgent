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

    response = await client.post(
        "/stream",
        json={
            "session_id": session_id,
            "selected_agent": "元智能体",
            "userinput": "帮我计算一组数字",
        },
    )
    body = (await response.get_data()).decode("utf-8")

    assert response.status_code == 200
    assert "OPENAI_API_KEY" in body
    assert "agent_updated" in body

    get_response = await client.get(
        "/stream",
        query_string={"userinput": "this must not appear in a URL"},
    )
    assert get_response.status_code == 405


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


@pytest.mark.asyncio
async def test_uploaded_file_is_private_to_owning_browser_user(tmp_path):
    app = build_app(tmp_path)
    owner = app.test_client()
    visitor = app.test_client()

    bootstrap = await owner.get("/api/bootstrap")
    session_id = (await bootstrap.get_json())["session"]["id"]
    upload_response = await owner.post(
        "/api/upload",
        form={"session_id": session_id},
        files={
            "file": FileStorage(
                stream=BytesIO(b"private demo file"),
                filename="notes.txt",
                name="file",
            )
        },
    )
    upload = (await upload_response.get_json())["upload"]

    own_response = await owner.get(upload["url_path"])
    await visitor.get("/api/bootstrap")
    visitor_response = await visitor.get(upload["url_path"])

    assert own_response.status_code == 200
    assert await own_response.get_data() == b"private demo file"
    assert visitor_response.status_code == 404
