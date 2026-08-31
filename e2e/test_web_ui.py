from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]


def _unused_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_for_server(url: str, process: subprocess.Popen[str]) -> None:
    for _ in range(60):
        if process.poll() is not None:
            stdout, _ = process.communicate()
            raise AssertionError(f"MetaAgent stopped before startup:\n{stdout}")
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                if response.status == 200:
                    return
        except OSError:
            time.sleep(0.25)
    raise AssertionError("MetaAgent did not start within 15 seconds")


def test_chat_and_mobile_layout(tmp_path):
    port = _unused_port()
    base_url = f"http://127.0.0.1:{port}"
    environment = os.environ.copy()
    environment.update(
        {
            "OPENAI_API_KEY": "",
            "SECRET_KEY": "e2e-local-only",
            "METAAGENT_DATA_DIR": str(tmp_path / "data"),
        }
    )
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "hypercorn",
            "app:app",
            "--bind",
            f"127.0.0.1:{port}",
        ],
        cwd=ROOT,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    try:
        _wait_for_server(base_url, process)
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            console_errors: list[str] = []
            stream_requests: list[tuple[str, str]] = []
            page.on(
                "console",
                lambda message: console_errors.append(message.text)
                if message.type == "error"
                else None,
            )
            page.on(
                "request",
                lambda request: stream_requests.append((request.url, request.method))
                if request.url.endswith("/stream")
                else None,
            )

            page.goto(base_url)
            page.get_by_placeholder("描述你的任务，或输入 @ 选择智能体").fill(
                "帮我计算 12 加 30"
            )
            page.get_by_role("button", name="发送").click()
            page.get_by_text("基础计算助手", exact=True).last.wait_for()
            page.get_by_text("当前未配置").wait_for()

            assert page.locator(".empty-chat").count() == 0
            assert stream_requests == [(f"{base_url}/stream", "POST")]

            page.set_viewport_size({"width": 390, "height": 844})
            page.get_by_role("button", name="切换侧边栏").click()
            assert "open" in (page.locator("#sidebar").get_attribute("class") or "")
            page.get_by_role("button", name="切换主题").click()
            assert page.evaluate("localStorage.getItem('theme')") in {"dark", "light"}
            assert console_errors == []
            browser.close()
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
