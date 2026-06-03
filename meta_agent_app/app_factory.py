from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, AsyncIterator

from quart import Quart, Response, jsonify, make_response, render_template, request, send_from_directory
from werkzeug.utils import secure_filename

from .agents import AgentService, USER_AVATAR
from .config import Settings
from .llm import LLMService
from .mcp_client import MCPClientManager
from .storage import SQLiteStore


ALLOWED_EXTENSIONS = {
    ".txt",
    ".pdf",
    ".doc",
    ".docx",
    ".xlsx",
    ".xls",
    ".csv",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".wav",
    ".mp3",
    ".m4a",
}


def create_app(settings: Settings | None = None) -> Quart:
    settings = settings or Settings.load()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.upload_dir.mkdir(parents=True, exist_ok=True)

    store = SQLiteStore(settings.database_path)
    store.initialize()
    agents = AgentService(settings, store)
    llm = LLMService(settings)
    mcp_client = MCPClientManager(settings)

    app = Quart(__name__, static_folder=str(settings.base_dir / "static"), template_folder=str(settings.base_dir / "templates"))
    app.secret_key = settings.secret_key
    app.config["MAX_CONTENT_LENGTH"] = 50 * 1000 * 1000
    app.extensions["settings"] = settings
    app.extensions["store"] = store
    app.extensions["agents"] = agents
    app.extensions["llm"] = llm
    app.extensions["mcp_client"] = mcp_client

    @app.after_serving
    async def close_mcp() -> None:
        await mcp_client.close()

    @app.route("/")
    async def index() -> Response:
        response = await make_response(await render_template("index.html"))
        _set_security_headers(response)
        user_id, is_new = _ensure_user(request, store, agents)
        if is_new:
            response.set_cookie("user_id", user_id, httponly=True, samesite="Lax")
        return response

    @app.route("/api/bootstrap")
    async def bootstrap() -> Response:
        user_id, is_new = _ensure_user(request, store, agents)
        session = store.get_or_create_session(user_id, request.args.get("session_id"))
        payload = _bootstrap_payload(user_id, session["id"], store, agents)
        response = await make_response(jsonify(payload))
        if is_new:
            response.set_cookie("user_id", user_id, httponly=True, samesite="Lax")
        return response

    @app.route("/api/sessions", methods=["GET", "POST"])
    async def sessions_api() -> Response:
        user_id, is_new = _ensure_user(request, store, agents)
        if request.method == "POST":
            data = await request.get_json(silent=True) or {}
            session = store.create_session(
                user_id,
                title=data.get("title") or "新对话",
                selected_agent=data.get("selected_agent") or "元智能体",
            )
            payload = {"session": session, "sessions": store.list_sessions(user_id), "messages": []}
        else:
            payload = {"sessions": store.list_sessions(user_id)}
        response = await make_response(jsonify(payload))
        if is_new:
            response.set_cookie("user_id", user_id, httponly=True, samesite="Lax")
        return response

    @app.route("/api/sessions/<session_id>", methods=["GET", "PATCH", "DELETE"])
    async def session_api(session_id: str) -> Response:
        user_id, _ = _ensure_user(request, store, agents)
        if request.method == "GET":
            session = store.get_or_create_session(user_id, session_id)
            return jsonify(
                {
                    "session": session,
                    "messages": store.list_messages(user_id, session["id"]),
                }
            )
        if request.method == "PATCH":
            data = await request.get_json(silent=True) or {}
            session = store.rename_session(user_id, session_id, data.get("title", "新对话"))
            if not session:
                return jsonify({"error": "Session not found"}), 404
            return jsonify({"session": session, "sessions": store.list_sessions(user_id)})

        store.delete_session(user_id, session_id)
        next_session = store.get_or_create_session(user_id)
        return jsonify(
            {
                "session": next_session,
                "sessions": store.list_sessions(user_id),
                "messages": store.list_messages(user_id, next_session["id"]),
            }
        )

    @app.route("/api/sessions/delete_all", methods=["POST"])
    async def delete_all_sessions() -> Response:
        user_id, _ = _ensure_user(request, store, agents)
        session = store.delete_all_sessions(user_id)
        return jsonify({"session": session, "sessions": store.list_sessions(user_id), "messages": []})

    @app.route("/api/agents", methods=["GET"])
    async def agents_api() -> Response:
        user_id, _ = _ensure_user(request, store, agents)
        return jsonify({"agents": agents.list_agents(user_id), "catalog": agents.catalog})

    @app.route("/api/agents/reset", methods=["POST"])
    async def reset_agents_api() -> Response:
        user_id, _ = _ensure_user(request, store, agents)
        return jsonify({"agents": agents.reset_user_agents(user_id)})

    @app.route("/api/upload", methods=["POST"])
    async def upload_api() -> Response:
        user_id, _ = _ensure_user(request, store, agents)
        form = await request.form
        files = await request.files
        session = store.get_or_create_session(user_id, form.get("session_id"))
        file = files.get("file")
        if not file or not file.filename:
            return jsonify({"success": False, "error": "No file uploaded"}), 400

        original_name = file.filename
        extension = Path(original_name).suffix.lower()
        if extension not in ALLOWED_EXTENSIONS:
            return jsonify({"success": False, "error": f"File type {extension} is not allowed"}), 400

        safe_name = secure_filename(original_name) or f"upload{extension}"
        stored_name = f"{uuid.uuid4().hex}_{safe_name}"
        target_dir = settings.upload_dir / user_id / session["id"]
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / stored_name
        await file.save(target_path)

        url_path = f"/uploads/{user_id}/{session['id']}/{stored_name}"
        upload = store.save_upload(user_id, session["id"], original_name, stored_name, target_path, url_path)
        message = store.add_message(
            user_id,
            session["id"],
            role="user",
            content=f"已上传文件：{original_name} ({url_path})",
            avatar=USER_AVATAR,
        )
        return jsonify({"success": True, "upload": upload, "message": message, "session": store.get_session(user_id, session["id"])})

    @app.route("/uploads/<user_id>/<session_id>/<path:filename>")
    async def uploaded_file(user_id: str, session_id: str, filename: str) -> Response:
        directory = settings.upload_dir / user_id / session_id
        return await send_from_directory(directory, filename, as_attachment=False)

    @app.route("/stream")
    async def stream_api() -> Response:
        user_id, _ = _ensure_user(request, store, agents)
        session = store.get_or_create_session(user_id, request.args.get("session_id"))
        user_input = (request.args.get("userinput") or "").strip()
        selected_agent = request.args.get("selected_agent") or session["selected_agent"] or "元智能体"

        async def generate() -> AsyncIterator[str]:
            if not user_input:
                yield _sse({"type": "error", "content": "请输入消息后再发送。"})
                yield _sse({"type": "end"})
                return

            user_agents = agents.list_agents(user_id)
            mentioned_agent, cleaned_input = agents.parse_mentions(user_input, user_agents)
            if mentioned_agent:
                selected = mentioned_agent
                user_text = cleaned_input
            else:
                selected = selected_agent
                user_text = user_input

            agent, description = agents.describe_agent(selected, user_agents)
            if not agent:
                selected = "元智能体"
                agent, description = agents.describe_agent(selected, user_agents)
            store.update_session_agent(user_id, session["id"], selected)
            store.add_message(user_id, session["id"], "user", user_text, avatar=USER_AVATAR)
            yield _sse({"type": "meta", "selected_agent": selected, "selected_agent_avatar": (agent or {}).get("avatar")})

            if selected == "元智能体":
                async for event in _run_meta_agent(user_id, session["id"], user_text, store, agents, llm):
                    yield event
                return

            async for event in _run_worker_agent(
                user_id,
                session["id"],
                selected,
                description,
                user_agents,
                store,
                agents,
                llm,
                mcp_client,
                settings,
            ):
                yield event

        return Response(generate(), mimetype="text/event-stream", headers={"Cache-Control": "no-cache"})

    return app


async def _run_meta_agent(
    user_id: str,
    session_id: str,
    user_text: str,
    store: SQLiteStore,
    agents: AgentService,
    llm: LLMService,
) -> AsyncIterator[str]:
    if not llm.configured:
        payload = agents.infer_agent_payload(user_text)
        content = (
            "当前未配置 `OPENAI_API_KEY`，已使用本地规则为你匹配一个演示智能体。\n\n"
            f"```json\n{json.dumps(payload, ensure_ascii=False)}\n```"
        )
        stored_agent = agents.upsert_agent_from_payload(user_id, payload)
        store.add_message(user_id, session_id, "assistant", content, name="元智能体", avatar=stored_agent.get("avatar"))
        yield _sse({"type": "content", "content": content})
        yield _sse({"type": "agent_updated", "agent": stored_agent})
        yield _sse({"type": "end"})
        return

    meta_prompt = _read_text(agents.settings.meta_agent_prompt_path, "你是元智能体。")
    prompt = (
        f"{meta_prompt}\n\n"
        f"可用工具目录如下：\n{agents.catalog_prompt()}\n\n"
        f"用户问题：{user_text}\n\n"
        "请先简短说明任务拆解，再输出一个 JSON 对象，格式为 "
        '{"name": "智能体名称", "servers": ["工具类别名称"]}。'
    )
    messages = [{"role": "user", "content": prompt}]
    full_content = ""
    try:
        completion = await llm.stream_chat(messages)
        async for chunk in completion:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            content = getattr(delta, "content", "") or ""
            if content:
                full_content += content
                yield _sse({"type": "content", "content": content})
    except Exception as exc:
        full_content = f"元智能体调用失败：{exc}"
        yield _sse({"type": "error", "content": full_content})

    stored_agent = None
    payload = agents.extract_agent_payload(full_content)
    if payload:
        stored_agent = agents.upsert_agent_from_payload(user_id, payload)
        label = "已创建智能体" if stored_agent.get("created") else "已有智能体"
        feedback = f"\n\n**{label}：{stored_agent['name']}**"
        full_content += feedback
        yield _sse({"type": "content", "content": feedback})
        yield _sse({"type": "agent_updated", "agent": stored_agent})

    store.add_message(
        user_id,
        session_id,
        "assistant",
        full_content,
        name="元智能体",
        avatar=(stored_agent or {}).get("avatar"),
    )
    yield _sse({"type": "end"})


async def _run_worker_agent(
    user_id: str,
    session_id: str,
    selected_agent: str,
    description: str,
    user_agents: list[dict[str, Any]],
    store: SQLiteStore,
    agents: AgentService,
    llm: LLMService,
    mcp_client: MCPClientManager,
    settings: Settings,
) -> AsyncIterator[str]:
    if not llm.configured:
        content = "当前未配置 `OPENAI_API_KEY`，请复制 `.env.example` 为 `.env` 并设置模型密钥后再发起真实对话。"
        store.add_message(user_id, session_id, "assistant", content, name=selected_agent)
        yield _sse({"type": "content", "content": content})
        yield _sse({"type": "end"})
        return

    try:
        await mcp_client.ensure_connected()
    except Exception as exc:
        yield _sse({"type": "error", "content": f"MCP 初始化失败：{exc}"})

    allowed_names = agents.allowed_tool_names(selected_agent, user_agents)
    tools = mcp_client.filter_tools(allowed_names)
    history = store.list_messages(user_id, session_id, limit=settings.max_messages)
    messages = _build_llm_messages(settings, selected_agent, description, history)
    full_display = ""

    for _ in range(4):
        completion = await llm.stream_chat(messages, tools)
        content = ""
        call_chunks: dict[int, dict[str, Any]] = {}
        async for chunk in completion:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            delta_content = getattr(delta, "content", "") or ""
            if delta_content:
                content += delta_content
                full_display += delta_content
                yield _sse({"type": "content", "content": delta_content})
            for tool_call in getattr(delta, "tool_calls", None) or []:
                _merge_tool_call_delta(call_chunks, tool_call)
        tool_calls = [call_chunks[index] for index in sorted(call_chunks)]
        if not tool_calls:
            store.add_message(user_id, session_id, "assistant", full_display, name=selected_agent)
            yield _sse({"type": "end"})
            return

        assistant_tool_message = {"role": "assistant", "content": content or "", "tool_calls": tool_calls}
        messages.append(assistant_tool_message)
        for tool_call in tool_calls:
            tool_name = tool_call["function"]["name"]
            raw_arguments = tool_call["function"].get("arguments") or "{}"
            try:
                arguments = json.loads(raw_arguments)
            except json.JSONDecodeError:
                arguments = {}
            yield _sse({"type": "tool_call", "name": tool_name, "arguments": arguments})
            result = await mcp_client.call_tool(tool_name, arguments)
            result_content = result.get("content", "")
            full_display += f"\n\n工具 `{tool_name}` 调用结果：\n{result_content}\n"
            yield _sse({"type": "tool_result", "name": tool_name, "content": result_content, "is_error": result.get("is_error")})
            messages.append({"role": "tool", "tool_call_id": tool_call["id"], "content": result_content})

    warning = "\n\n工具调用轮次已达到上限，请缩小任务范围后重试。"
    full_display += warning
    store.add_message(user_id, session_id, "assistant", full_display, name=selected_agent)
    yield _sse({"type": "content", "content": warning})
    yield _sse({"type": "end"})


def _merge_tool_call_delta(calls: dict[int, dict[str, Any]], tool_call: Any) -> None:
    index = getattr(tool_call, "index", 0) or 0
    entry = calls.setdefault(
        index,
        {"id": "", "type": "function", "function": {"name": "", "arguments": ""}},
    )
    if getattr(tool_call, "id", None):
        entry["id"] = tool_call.id
    if getattr(tool_call, "type", None):
        entry["type"] = tool_call.type
    function = getattr(tool_call, "function", None)
    if function:
        if getattr(function, "name", None):
            entry["function"]["name"] += function.name
        if getattr(function, "arguments", None):
            entry["function"]["arguments"] += function.arguments


def _build_llm_messages(settings: Settings, selected_agent: str, description: str, history: list[dict[str, Any]]) -> list[dict[str, Any]]:
    system_prompt = _read_text(settings.system_prompt_path, "你是一个智能助手。")
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": system_prompt},
        {
            "role": "system",
            "content": (
                f"当前智能体：{selected_agent}\n"
                f"当前可用能力：\n{description or '仅使用通用对话能力。'}\n"
                "如需工具，请直接调用工具，不要假装调用。"
            ),
        },
    ]
    for item in history:
        if item["role"] in {"user", "assistant"}:
            messages.append({"role": item["role"], "content": item["content"]})
    return messages


def _bootstrap_payload(user_id: str, session_id: str, store: SQLiteStore, agents: AgentService) -> dict[str, Any]:
    return {
        "user_id": user_id,
        "session": store.get_or_create_session(user_id, session_id),
        "sessions": store.list_sessions(user_id),
        "agents": agents.list_agents(user_id),
        "messages": store.list_messages(user_id, session_id),
        "catalog": agents.catalog,
    }


def _ensure_user(request_obj: Any, store: SQLiteStore, agents: AgentService) -> tuple[str, bool]:
    user_id = request_obj.cookies.get("user_id")
    is_new = False
    if not user_id:
        user_id = str(uuid.uuid4())
        is_new = True
    store.ensure_user(user_id)
    agents.ensure_user_defaults(user_id)
    return user_id, is_new


def _read_text(path: Path, fallback: str) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return fallback


def _sse(payload: dict[str, Any]) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def _set_security_headers(response: Response) -> None:
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: blob:; "
        "media-src 'self' https: blob:; "
        "connect-src 'self'; "
        "object-src 'none'; "
        "base-uri 'self'; "
        "frame-ancestors 'none'"
    )
    response.headers["X-Content-Type-Options"] = "nosniff"
