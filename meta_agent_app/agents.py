from __future__ import annotations

import json
import random
import re
from pathlib import Path
from typing import Any

from .config import Settings
from .storage import SQLiteStore


USER_AVATAR = "/static/img/avatars/user.svg"
DEFAULT_AGENT_AVATAR = "/static/img/avatars/meta_agent.svg"


class AgentService:
    def __init__(self, settings: Settings, store: SQLiteStore):
        self.settings = settings
        self.store = store
        self.catalog = self._load_json(settings.base_dir / "meta.json", default=[])
        self.default_agents = self._load_json(settings.base_dir / "agents.json", default=[])
        self.catalog_by_name = {item["name"]: item for item in self.catalog}

    def ensure_user_defaults(self, user_id: str) -> None:
        self.store.ensure_default_agents(user_id, self.default_agents)

    def reset_user_agents(self, user_id: str) -> list[dict[str, Any]]:
        return self.store.reset_agents(user_id, self.default_agents)

    def list_agents(self, user_id: str) -> list[dict[str, Any]]:
        agents = self.store.list_agents(user_id)
        if not agents:
            self.ensure_user_defaults(user_id)
            agents = self.store.list_agents(user_id)
        return agents

    def parse_mentions(self, user_input: str, agents: list[dict[str, Any]]) -> tuple[str | None, str]:
        agent_names = {agent["name"] for agent in agents}
        matches = re.findall(r"@([^@\s]+)", user_input or "")
        selected = next((name for name in matches if name in agent_names), None)
        cleaned = user_input or ""
        if selected:
            cleaned = cleaned.replace(f"@{selected}", "", 1).strip()
        return selected, cleaned

    def describe_agent(self, agent_name: str, agents: list[dict[str, Any]]) -> tuple[dict[str, Any] | None, str]:
        agent = next((item for item in agents if item["name"] == agent_name), None)
        if not agent:
            return None, ""
        descriptions = []
        for server_name in agent.get("servers", []):
            item = self.catalog_by_name.get(server_name)
            if item:
                descriptions.append(f"{item['name']}：{item.get('description', '')}")
        return agent, "\n".join(descriptions)

    def allowed_tool_names(self, agent_name: str, agents: list[dict[str, Any]]) -> set[str]:
        agent = next((item for item in agents if item["name"] == agent_name), None)
        if not agent:
            return set()
        allowed: set[str] = set()
        for server_name in agent.get("servers", []):
            item = self.catalog_by_name.get(server_name)
            allowed.update(item.get("tools", []) if item else [])
        return allowed

    def upsert_agent_from_payload(self, user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        name = str(payload.get("name") or "组合智能体").strip()[:30]
        servers = self.normalize_servers(payload.get("servers", []))
        existing = self.find_agent_by_servers(user_id, servers)
        if existing:
            return {**existing, "created": False}
        agent = {
            "name": self._unique_agent_name(user_id, name),
            "servers": servers,
            "avatar": self.pick_avatar(user_id),
        }
        stored = self.store.upsert_agent(user_id, agent)
        return {**stored, "created": True}

    def normalize_servers(self, servers: Any) -> list[str]:
        if isinstance(servers, str):
            servers = [servers]
        valid = []
        for item in servers or []:
            name = str(item).strip()
            if name in self.catalog_by_name and name not in valid:
                valid.append(name)
        return valid

    def find_agent_by_servers(self, user_id: str, servers: list[str]) -> dict[str, Any] | None:
        target = sorted(servers)
        for agent in self.list_agents(user_id):
            if sorted(agent.get("servers", [])) == target:
                return agent
        return None

    def pick_avatar(self, user_id: str) -> str:
        used = {agent.get("avatar") for agent in self.list_agents(user_id)}
        avatar_dir = self.settings.base_dir / "static" / "img" / "avatars"
        candidates = []
        for path in avatar_dir.glob("*"):
            if path.suffix.lower() in {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"}:
                url = f"/static/img/avatars/{path.name}"
                if url not in used and path.name != "user.svg":
                    candidates.append(url)
        return random.choice(candidates) if candidates else DEFAULT_AGENT_AVATAR

    def extract_agent_payload(self, content: str) -> dict[str, Any] | None:
        for match in reversed(list(re.finditer(r"\{.*?\}", content or "", re.DOTALL))):
            try:
                data = json.loads(match.group(0))
            except json.JSONDecodeError:
                continue
            if isinstance(data, dict) and "servers" in data:
                return data
        return None

    def infer_agent_payload(self, user_input: str) -> dict[str, Any]:
        text = user_input.lower()
        servers: list[str] = []
        keyword_map = {
            "基础计算": ["计算", "方程", "均值", "标准差", "矩阵", "导数", "积分", "math", "calculate"],
            "数据分析": ["数据", "分类", "聚类", "降维", "机器学习", "csv", "excel"],
        }
        for server, keywords in keyword_map.items():
            if server in self.catalog_by_name and any(keyword in text for keyword in keywords):
                servers.append(server)
        readable = "".join(server.replace("工具", "") for server in servers) or "通用"
        return {"name": f"{readable}助手", "servers": servers}

    def catalog_prompt(self) -> str:
        return json.dumps(self.catalog, ensure_ascii=False, indent=2)

    def _unique_agent_name(self, user_id: str, base_name: str) -> str:
        existing = {agent["name"] for agent in self.list_agents(user_id)}
        if base_name not in existing:
            return base_name
        for index in range(2, 100):
            candidate = f"{base_name}{index}"
            if candidate not in existing:
                return candidate
        return f"{base_name}-{random.randint(1000, 9999)}"

    @staticmethod
    def _load_json(path: Path, default: Any) -> Any:
        if not path.exists():
            return default
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
