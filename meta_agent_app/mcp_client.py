from __future__ import annotations

import json
import os
import re
from contextlib import AsyncExitStack
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client

from .config import Settings


class MCPClientManager:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.exit_stack = AsyncExitStack()
        self.connected = False
        self.available_tools: dict[str, dict[str, Any]] = {}
        self.tool_sessions: dict[str, ClientSession] = {}
        self._sse_contexts: list[Any] = []

    async def ensure_connected(self, force: bool = False) -> None:
        if self.connected and not force:
            return
        if force:
            await self.close()
        config = self._load_config()
        for server_name, server_config in config.get("mcpServers", {}).items():
            if server_config.get("disabled", False):
                continue
            try:
                if server_config.get("url"):
                    await self._connect_sse(server_name, server_config)
                else:
                    await self._connect_stdio(server_name, server_config)
            except Exception as exc:
                print(f"MCP server '{server_name}' skipped: {exc}")
        self.connected = True

    def filter_tools(self, allowed_names: set[str]) -> list[dict[str, Any]]:
        if not allowed_names:
            return []
        return [tool["schema"] for name, tool in self.available_tools.items() if name in allowed_names]

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        session = self.tool_sessions.get(name)
        if not session:
            return {"is_error": True, "content": f"Tool '{name}' is not available."}
        result = await session.call_tool(name, arguments or {})
        parts = []
        for item in result.content:
            if hasattr(item, "text"):
                parts.append(item.text)
            else:
                parts.append(str(item))
        return {
            "is_error": bool(result.isError),
            "content": "\n".join(parts),
            "meta": result.meta,
        }

    async def close(self) -> None:
        try:
            await self.exit_stack.aclose()
        except BaseExceptionGroup as exc:
            if not _is_cancel_scope_shutdown(exc):
                raise
            print(f"MCP shutdown warning: {exc}")
        except RuntimeError as exc:
            if "cancel scope" not in str(exc):
                raise
            print(f"MCP shutdown warning: {exc}")
        self.exit_stack = AsyncExitStack()
        self.connected = False
        self.available_tools.clear()
        self.tool_sessions.clear()
        self._sse_contexts.clear()

    async def _connect_stdio(self, server_name: str, server_config: dict[str, Any]) -> None:
        command = self._resolve_command(server_config.get("command", ""))
        args = [self._expand_env(str(arg)) for arg in server_config.get("args", [])]
        env = {**os.environ, **{k: self._expand_env(str(v)) for k, v in server_config.get("env", {}).items()}}
        params = StdioServerParameters(command=command, args=args, env=env)
        stdio, write = await self.exit_stack.enter_async_context(stdio_client(params))
        session = await self.exit_stack.enter_async_context(ClientSession(stdio, write))
        await session.initialize()
        await self._register_tools(server_name, session)

    async def _connect_sse(self, server_name: str, server_config: dict[str, Any]) -> None:
        url = self._expand_env(server_config["url"])
        streams = await self.exit_stack.enter_async_context(sse_client(url=url))
        session = await self.exit_stack.enter_async_context(ClientSession(*streams))
        await session.initialize()
        await self._register_tools(server_name, session)

    async def _register_tools(self, server_name: str, session: ClientSession) -> None:
        response = await session.list_tools()
        for tool in response.tools:
            schema = {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": tool.inputSchema,
                },
            }
            self.available_tools[tool.name] = {"server": server_name, "schema": schema}
            self.tool_sessions[tool.name] = session

    def _load_config(self) -> dict[str, Any]:
        path = self.settings.mcp_server_config_path
        if not path.exists():
            return {"mcpServers": {}}
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _resolve_command(self, command: str) -> str:
        command_lower = command.lower()
        if command_lower == "python":
            return self.settings.python_path
        if command_lower == "node":
            return self.settings.node_path
        if command_lower == "npx":
            return self.settings.npx_path
        return command

    @staticmethod
    def _expand_env(value: str) -> str:
        pattern = re.compile(r"\$\{([A-Z0-9_]+)(?::-(.*?))?\}")

        def replace(match: re.Match[str]) -> str:
            name, default = match.group(1), match.group(2)
            return os.getenv(name, default or "")

        return pattern.sub(replace, value)


def public_file_url(path: Path, root: Path) -> str:
    return "/" + path.relative_to(root).as_posix()


def _is_cancel_scope_shutdown(exc: BaseException) -> bool:
    if isinstance(exc, BaseExceptionGroup):
        return all(_is_cancel_scope_shutdown(item) for item in exc.exceptions)
    return isinstance(exc, RuntimeError) and "cancel scope" in str(exc)
