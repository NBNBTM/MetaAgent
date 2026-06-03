from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class SQLiteStore:
    def __init__(self, database_path: Path):
        self.database_path = database_path
        self._lock = threading.RLock()

    def initialize(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.executescript(
                """
                PRAGMA journal_mode = WAL;

                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    selected_agent TEXT NOT NULL DEFAULT '元智能体',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_sessions_user_updated
                ON sessions(user_id, updated_at DESC);

                CREATE TABLE IF NOT EXISTS messages (
                    message_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    name TEXT,
                    avatar TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_messages_session_created
                ON messages(session_id, created_at ASC);

                CREATE TABLE IF NOT EXISTS agents (
                    agent_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    servers TEXT NOT NULL,
                    avatar TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE(user_id, name),
                    FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS uploads (
                    upload_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    original_name TEXT NOT NULL,
                    stored_name TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    url_path TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                    FOREIGN KEY(session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
                );
                """
            )

    def ensure_user(self, user_id: str) -> None:
        with self._lock, self._connect() as db:
            db.execute(
                "INSERT OR IGNORE INTO users(user_id, created_at) VALUES(?, ?)",
                (user_id, utc_now()),
            )

    def ensure_default_agents(self, user_id: str, agents: list[dict[str, Any]]) -> None:
        if self.list_agents(user_id):
            return
        with self._lock, self._connect() as db:
            for agent in agents:
                db.execute(
                    """
                    INSERT OR IGNORE INTO agents(agent_id, user_id, name, servers, avatar, created_at)
                    VALUES(?, ?, ?, ?, ?, ?)
                    """,
                    (
                        _new_id(),
                        user_id,
                        agent["name"],
                        json.dumps(agent.get("servers", []), ensure_ascii=False),
                        agent.get("avatar", ""),
                        utc_now(),
                    ),
                )

    def reset_agents(self, user_id: str, agents: list[dict[str, Any]]) -> list[dict[str, Any]]:
        with self._lock, self._connect() as db:
            db.execute("DELETE FROM agents WHERE user_id = ?", (user_id,))
            for agent in agents:
                db.execute(
                    """
                    INSERT INTO agents(agent_id, user_id, name, servers, avatar, created_at)
                    VALUES(?, ?, ?, ?, ?, ?)
                    """,
                    (
                        _new_id(),
                        user_id,
                        agent["name"],
                        json.dumps(agent.get("servers", []), ensure_ascii=False),
                        agent.get("avatar", ""),
                        utc_now(),
                    ),
                )
        return self.list_agents(user_id)

    def list_agents(self, user_id: str) -> list[dict[str, Any]]:
        with self._lock, self._connect() as db:
            rows = db.execute(
                "SELECT agent_id, name, servers, avatar, created_at FROM agents WHERE user_id = ? ORDER BY created_at ASC",
                (user_id,),
            ).fetchall()
        return [
            {
                "id": row["agent_id"],
                "name": row["name"],
                "servers": json.loads(row["servers"]),
                "avatar": row["avatar"],
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    def upsert_agent(self, user_id: str, agent: dict[str, Any]) -> dict[str, Any]:
        now = utc_now()
        with self._lock, self._connect() as db:
            db.execute(
                """
                INSERT INTO agents(agent_id, user_id, name, servers, avatar, created_at)
                VALUES(?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id, name) DO UPDATE SET
                    servers = excluded.servers,
                    avatar = excluded.avatar
                """,
                (
                    _new_id(),
                    user_id,
                    agent["name"],
                    json.dumps(agent.get("servers", []), ensure_ascii=False),
                    agent.get("avatar", ""),
                    now,
                ),
            )
        stored = [item for item in self.list_agents(user_id) if item["name"] == agent["name"]]
        return stored[0]

    def create_session(self, user_id: str, title: str = "新对话", selected_agent: str = "元智能体") -> dict[str, Any]:
        session = {
            "id": _new_id(),
            "title": title,
            "selected_agent": selected_agent,
            "created_at": utc_now(),
            "updated_at": utc_now(),
            "message_count": 0,
        }
        with self._lock, self._connect() as db:
            db.execute(
                """
                INSERT INTO sessions(session_id, user_id, title, selected_agent, created_at, updated_at)
                VALUES(?, ?, ?, ?, ?, ?)
                """,
                (
                    session["id"],
                    user_id,
                    title,
                    selected_agent,
                    session["created_at"],
                    session["updated_at"],
                ),
            )
        return session

    def get_or_create_session(self, user_id: str, session_id: str | None = None) -> dict[str, Any]:
        if session_id:
            session = self.get_session(user_id, session_id)
            if session:
                return session
        sessions = self.list_sessions(user_id)
        if sessions:
            return sessions[0]
        return self.create_session(user_id)

    def get_session(self, user_id: str, session_id: str) -> dict[str, Any] | None:
        with self._lock, self._connect() as db:
            row = db.execute(
                """
                SELECT s.*, COUNT(m.message_id) AS message_count
                FROM sessions s
                LEFT JOIN messages m ON m.session_id = s.session_id
                WHERE s.user_id = ? AND s.session_id = ?
                GROUP BY s.session_id
                """,
                (user_id, session_id),
            ).fetchone()
        return _session_from_row(row) if row else None

    def list_sessions(self, user_id: str) -> list[dict[str, Any]]:
        with self._lock, self._connect() as db:
            rows = db.execute(
                """
                SELECT s.*, COUNT(m.message_id) AS message_count
                FROM sessions s
                LEFT JOIN messages m ON m.session_id = s.session_id
                WHERE s.user_id = ?
                GROUP BY s.session_id
                ORDER BY s.updated_at DESC
                """,
                (user_id,),
            ).fetchall()
        return [_session_from_row(row) for row in rows]

    def rename_session(self, user_id: str, session_id: str, title: str) -> dict[str, Any] | None:
        with self._lock, self._connect() as db:
            db.execute(
                "UPDATE sessions SET title = ?, updated_at = ? WHERE user_id = ? AND session_id = ?",
                (title.strip() or "新对话", utc_now(), user_id, session_id),
            )
        return self.get_session(user_id, session_id)

    def update_session_agent(self, user_id: str, session_id: str, selected_agent: str) -> None:
        with self._lock, self._connect() as db:
            db.execute(
                "UPDATE sessions SET selected_agent = ?, updated_at = ? WHERE user_id = ? AND session_id = ?",
                (selected_agent, utc_now(), user_id, session_id),
            )

    def delete_session(self, user_id: str, session_id: str) -> None:
        with self._lock, self._connect() as db:
            db.execute("DELETE FROM sessions WHERE user_id = ? AND session_id = ?", (user_id, session_id))

    def delete_all_sessions(self, user_id: str) -> dict[str, Any]:
        with self._lock, self._connect() as db:
            db.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
        return self.create_session(user_id)

    def list_messages(self, user_id: str, session_id: str, limit: int | None = None) -> list[dict[str, Any]]:
        if not self.get_session(user_id, session_id):
            return []
        with self._lock, self._connect() as db:
            rows = db.execute(
                """
                SELECT message_id, role, content, name, avatar, created_at
                FROM messages
                WHERE session_id = ?
                ORDER BY created_at ASC
                """,
                (session_id,),
            ).fetchall()
        if limit:
            rows = rows[-limit:]
        return [
            {
                "id": row["message_id"],
                "role": row["role"],
                "content": row["content"],
                "name": row["name"],
                "avatar": row["avatar"],
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    def add_message(
        self,
        user_id: str,
        session_id: str,
        role: str,
        content: str,
        name: str | None = None,
        avatar: str | None = None,
    ) -> dict[str, Any]:
        if not self.get_session(user_id, session_id):
            raise ValueError("session not found")
        message = {
            "id": _new_id(),
            "role": role,
            "content": content,
            "name": name,
            "avatar": avatar,
            "created_at": utc_now(),
        }
        with self._lock, self._connect() as db:
            db.execute(
                """
                INSERT INTO messages(message_id, session_id, role, content, name, avatar, created_at)
                VALUES(?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    message["id"],
                    session_id,
                    role,
                    content,
                    name,
                    avatar,
                    message["created_at"],
                ),
            )
            db.execute(
                "UPDATE sessions SET updated_at = ? WHERE user_id = ? AND session_id = ?",
                (message["created_at"], user_id, session_id),
            )
        return message

    def save_upload(
        self,
        user_id: str,
        session_id: str,
        original_name: str,
        stored_name: str,
        file_path: Path,
        url_path: str,
    ) -> dict[str, Any]:
        upload = {
            "id": _new_id(),
            "original_name": original_name,
            "stored_name": stored_name,
            "file_path": str(file_path),
            "url_path": url_path,
            "created_at": utc_now(),
        }
        with self._lock, self._connect() as db:
            db.execute(
                """
                INSERT INTO uploads(upload_id, user_id, session_id, original_name, stored_name, file_path, url_path, created_at)
                VALUES(?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    upload["id"],
                    user_id,
                    session_id,
                    original_name,
                    stored_name,
                    str(file_path),
                    url_path,
                    upload["created_at"],
                ),
            )
        return upload

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.database_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn


def _new_id() -> str:
    return str(uuid.uuid4())


def _session_from_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["session_id"],
        "title": row["title"],
        "selected_agent": row["selected_agent"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "message_count": row["message_count"],
    }
