from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _as_int(value: str | None, default: int) -> int:
    try:
        return int(value) if value not in (None, "") else default
    except ValueError:
        return default


def _as_float(value: str | None, default: float) -> float:
    try:
        return float(value) if value not in (None, "") else default
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    base_dir: Path
    data_dir: Path
    upload_dir: Path
    database_path: Path
    openai_api_key: str
    openai_base_url: str | None
    model: str
    max_tokens: int
    temperature: float
    timeout: int
    max_messages: int
    system_prompt_path: Path
    meta_agent_prompt_path: Path
    mcp_server_config_path: Path
    python_path: str
    node_path: str
    npx_path: str
    debug: bool
    secret_key: str

    @classmethod
    def load(cls, base_dir: Path | None = None) -> "Settings":
        resolved_base = (base_dir or Path(__file__).resolve().parents[1]).resolve()
        load_dotenv(resolved_base / ".env")

        data_dir = _resolve_path(os.getenv("METAAGENT_DATA_DIR", "data"), resolved_base)
        upload_dir = _resolve_path(os.getenv("UPLOAD_DIR", "uploads"), data_dir)
        database_path = _resolve_path(os.getenv("DATABASE_PATH", "metaagent.sqlite3"), data_dir)

        model_list = [m.strip() for m in os.getenv("MODEL", "gpt-4o-mini").split(";") if m.strip()]
        model = model_list[0] if model_list else "gpt-4o-mini"

        return cls(
            base_dir=resolved_base,
            data_dir=data_dir,
            upload_dir=upload_dir,
            database_path=database_path,
            openai_api_key=os.getenv("OPENAI_API_KEY", "").strip(),
            openai_base_url=os.getenv("OPENAI_BASE_URL") or None,
            model=model,
            max_tokens=_as_int(os.getenv("MAX_TOKENS"), 4096),
            temperature=_as_float(os.getenv("TEMPERATURE"), 0.4),
            timeout=_as_int(os.getenv("TIMEOUT"), 120),
            max_messages=_as_int(os.getenv("MAX_MESSAGES"), 30),
            system_prompt_path=_resolve_path(os.getenv("SYSTEM_PROMPT", "prompt/system.md"), resolved_base),
            meta_agent_prompt_path=_resolve_path(os.getenv("META_AGENT_PROMPT", "prompt/meta_agent.md"), resolved_base),
            mcp_server_config_path=_resolve_path(
                os.getenv("MCP_SERVER_CONFIG_PATH", "mcp_server_config.json"),
                resolved_base,
            ),
            python_path=os.getenv("METAAGENT_PYTHON_PATH") or sys.executable,
            node_path=os.getenv("METAAGENT_NODE_PATH") or "node",
            npx_path=os.getenv("METAAGENT_NPX_PATH") or "npx",
            debug=_as_bool(os.getenv("DEBUG"), False),
            secret_key=os.getenv("SECRET_KEY", "metaagent-local-dev"),
        )


def _resolve_path(value: str, root: Path) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = root / path
    return path.resolve()
