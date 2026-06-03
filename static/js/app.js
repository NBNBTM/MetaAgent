const state = {
    session: null,
    sessions: [],
    agents: [],
    selectedAgent: "元智能体",
    streaming: false,
};

const els = {};

document.addEventListener("DOMContentLoaded", async () => {
    bindElements();
    bindEvents();
    initTheme();
    await bootstrap();
});

function bindElements() {
    els.sidebar = document.getElementById("sidebar");
    els.sidebarToggle = document.getElementById("sidebar-toggle");
    els.themeToggle = document.getElementById("theme-toggle");
    els.newSession = document.getElementById("new-session-btn");
    els.deleteCurrent = document.getElementById("delete-current-btn");
    els.deleteAll = document.getElementById("delete-all-btn");
    els.resetAgents = document.getElementById("reset-agents-btn");
    els.agentList = document.getElementById("agent-list");
    els.sessionList = document.getElementById("session-list");
    els.messages = document.getElementById("messages");
    els.title = document.getElementById("session-title");
    els.subtitle = document.getElementById("session-subtitle");
    els.form = document.getElementById("composer");
    els.input = document.getElementById("user-input");
    els.send = document.getElementById("send-btn");
    els.upload = document.getElementById("upload-btn");
    els.fileInput = document.getElementById("file-input");
    els.mentionBox = document.getElementById("mention-box");
}

function bindEvents() {
    els.sidebarToggle.addEventListener("click", () => els.sidebar.classList.toggle("open"));
    els.themeToggle.addEventListener("click", toggleTheme);
    els.newSession.addEventListener("click", createSession);
    els.deleteCurrent.addEventListener("click", deleteCurrentSession);
    els.deleteAll.addEventListener("click", deleteAllSessions);
    els.resetAgents.addEventListener("click", resetAgents);
    els.upload.addEventListener("click", () => els.fileInput.click());
    els.fileInput.addEventListener("change", uploadFile);
    els.form.addEventListener("submit", submitMessage);
    els.input.addEventListener("input", () => {
        autoResize(els.input);
        updateMentionBox();
    });
    els.input.addEventListener("keydown", (event) => {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            els.form.requestSubmit();
        }
        if (event.key === "Escape") {
            hideMentionBox();
        }
    });
    document.addEventListener("click", (event) => {
        if (!els.mentionBox.contains(event.target) && event.target !== els.input) {
            hideMentionBox();
        }
    });
}

async function bootstrap(sessionId = null) {
    const suffix = sessionId ? `?session_id=${encodeURIComponent(sessionId)}` : "";
    const data = await api(`/api/bootstrap${suffix}`);
    state.session = data.session;
    state.sessions = data.sessions || [];
    state.agents = data.agents || [];
    state.selectedAgent = state.session?.selected_agent || "元智能体";
    renderAll(data.messages || []);
}

async function api(url, options = {}) {
    const response = await fetch(url, {
        headers: {"Content-Type": "application/json", ...(options.headers || {})},
        ...options,
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
        throw new Error(data.error || `Request failed: ${response.status}`);
    }
    return data;
}

function renderAll(messages) {
    renderAgents();
    renderSessions();
    renderHeader();
    renderMessages(messages);
}

function renderHeader() {
    els.title.textContent = state.session?.title || "新对话";
    els.subtitle.textContent = `当前智能体：${state.selectedAgent}`;
}

function renderAgents() {
    replaceChildren(els.agentList);
    for (const agent of state.agents) {
        const button = document.createElement("button");
        button.type = "button";
        button.className = `agent-item ${agent.name === state.selectedAgent ? "active" : ""}`;
        button.addEventListener("click", () => {
            state.selectedAgent = agent.name;
            renderAgents();
            renderHeader();
            els.sidebar.classList.remove("open");
        });

        const img = document.createElement("img");
        img.src = agent.avatar || "/static/img/avatars/meta_agent.svg";
        img.alt = `${agent.name}头像`;

        const span = document.createElement("span");
        span.className = "agent-name";
        span.textContent = agent.name;

        button.append(img, span);
        els.agentList.append(button);
    }
}

function renderSessions() {
    replaceChildren(els.sessionList);
    if (!state.sessions.length) {
        const empty = document.createElement("p");
        empty.className = "session-meta";
        empty.textContent = "暂无会话";
        els.sessionList.append(empty);
        return;
    }

    for (const session of state.sessions) {
        const item = document.createElement("div");
        item.className = `session-item ${state.session?.id === session.id ? "active" : ""}`;

        const main = document.createElement("button");
        main.type = "button";
        main.className = "session-copy";
        main.addEventListener("click", () => loadSession(session.id));

        const name = document.createElement("div");
        name.className = "session-name";
        name.textContent = session.title;

        const meta = document.createElement("div");
        meta.className = "session-meta";
        meta.textContent = `${session.message_count || 0} 条消息`;

        const rename = document.createElement("button");
        rename.type = "button";
        rename.className = "rename-session";
        rename.textContent = "改名";
        rename.addEventListener("click", () => renameSession(session));

        main.append(name, meta);
        item.append(main, rename);
        els.sessionList.append(item);
    }
}

function renderMessages(messages) {
    replaceChildren(els.messages);
    if (!messages.length) {
        const empty = document.createElement("div");
        empty.className = "empty-chat";
        const box = document.createElement("div");
        const title = document.createElement("strong");
        title.textContent = "描述一个任务";
        const copy = document.createElement("span");
        copy.textContent = "元智能体会先判断需要哪些工具，再创建或选择合适的助手。";
        box.append(title, copy);
        empty.append(box);
        els.messages.append(empty);
        return;
    }
    for (const message of messages) {
        appendMessage(message.role, message.content, {
            name: message.name,
            avatar: message.avatar,
            markdown: message.role !== "user",
        });
    }
    scrollToBottom();
}

function appendMessage(role, content, options = {}) {
    const wrapper = document.createElement("article");
    wrapper.className = `message ${role}`;

    const avatar = document.createElement("img");
    avatar.className = "message-avatar";
    avatar.src = options.avatar || (role === "user" ? "/static/img/avatars/user.svg" : "/static/img/avatars/meta_agent.svg");
    avatar.alt = role === "user" ? "用户头像" : `${options.name || "智能体"}头像`;

    const stack = document.createElement("div");
    stack.className = "message-stack";

    if (role !== "user") {
        const name = document.createElement("div");
        name.className = "message-name";
        name.textContent = options.name || "智能体";
        stack.append(name);
    }

    const bubble = document.createElement("div");
    bubble.className = "bubble";
    if (options.markdown) {
        bubble.innerHTML = renderMarkdown(content || "");
    } else {
        bubble.textContent = content || "";
    }
    stack.append(bubble);
    wrapper.append(avatar, stack);
    els.messages.append(wrapper);
    scrollToBottom();
    return {wrapper, bubble, stack};
}

function createAssistantStream(agentName, avatar) {
    const node = appendMessage("assistant", "", {name: agentName, avatar, markdown: true});
    node.raw = "";
    return node;
}

function appendToolCard(stack, title, content, isError = false) {
    const card = document.createElement("div");
    card.className = `tool-card ${isError ? "error" : ""}`;
    card.textContent = `${title}\n${content || ""}`.trim();
    stack.append(card);
    scrollToBottom();
}

async function submitMessage(event) {
    event.preventDefault();
    const text = els.input.value.trim();
    if (!text || state.streaming || !state.session) return;

    setComposerEnabled(false);
    appendMessage("user", text, {markdown: false});
    els.input.value = "";
    autoResize(els.input);
    hideMentionBox();

    const params = new URLSearchParams({
        session_id: state.session.id,
        selected_agent: state.selectedAgent,
        userinput: text,
    });
    const source = new EventSource(`/stream?${params.toString()}`);
    let assistantNode = null;
    let closedByServer = false;

    source.onmessage = async (eventMessage) => {
        const data = JSON.parse(eventMessage.data);
        if (data.type === "meta") {
            assistantNode = createAssistantStream(data.selected_agent || state.selectedAgent, data.selected_agent_avatar);
            state.selectedAgent = data.selected_agent || state.selectedAgent;
            renderHeader();
            renderAgents();
            return;
        }
        if (!assistantNode) {
            assistantNode = createAssistantStream(state.selectedAgent);
        }
        if (data.type === "content") {
            assistantNode.raw += data.content || "";
            assistantNode.bubble.innerHTML = renderMarkdown(assistantNode.raw);
        }
        if (data.type === "tool_call") {
            appendToolCard(assistantNode.stack, `调用工具：${data.name}`, JSON.stringify(data.arguments || {}, null, 2));
        }
        if (data.type === "tool_result") {
            appendToolCard(assistantNode.stack, `工具结果：${data.name}`, data.content, data.is_error);
        }
        if (data.type === "agent_updated") {
            await refreshAgents();
        }
        if (data.type === "error") {
            appendToolCard(assistantNode.stack, "错误", data.content, true);
        }
        if (data.type === "end") {
            closedByServer = true;
            source.close();
            setComposerEnabled(true);
            await refreshSessions();
        }
        scrollToBottom();
    };

    source.onerror = async () => {
        source.close();
        if (!closedByServer && assistantNode) {
            appendToolCard(assistantNode.stack, "连接已结束", "如果回复不完整，请重试。", true);
        }
        setComposerEnabled(true);
        await refreshSessions();
    };
}

async function createSession() {
    const data = await api("/api/sessions", {method: "POST", body: JSON.stringify({title: "新对话"})});
    state.session = data.session;
    state.sessions = data.sessions || [];
    state.selectedAgent = state.session.selected_agent || "元智能体";
    renderAll([]);
    els.sidebar.classList.remove("open");
}

async function loadSession(sessionId) {
    const data = await api(`/api/sessions/${encodeURIComponent(sessionId)}`);
    state.session = data.session;
    state.selectedAgent = data.session.selected_agent || "元智能体";
    await refreshSessions(false);
    renderAll(data.messages || []);
    els.sidebar.classList.remove("open");
}

async function renameSession(session) {
    const title = prompt("输入新的会话名称", session.title);
    if (!title) return;
    const data = await api(`/api/sessions/${encodeURIComponent(session.id)}`, {
        method: "PATCH",
        body: JSON.stringify({title}),
    });
    state.session = data.session.id === state.session.id ? data.session : state.session;
    state.sessions = data.sessions || [];
    renderSessions();
    renderHeader();
}

async function deleteCurrentSession() {
    if (!state.session || !confirm("确定删除当前会话吗？")) return;
    const data = await api(`/api/sessions/${encodeURIComponent(state.session.id)}`, {method: "DELETE"});
    state.session = data.session;
    state.sessions = data.sessions || [];
    state.selectedAgent = state.session.selected_agent || "元智能体";
    renderAll(data.messages || []);
}

async function deleteAllSessions() {
    if (!confirm("确定清空全部会话吗？此操作不可恢复。")) return;
    const data = await api("/api/sessions/delete_all", {method: "POST"});
    state.session = data.session;
    state.sessions = data.sessions || [];
    state.selectedAgent = "元智能体";
    renderAll([]);
}

async function resetAgents() {
    if (!confirm("确定重置智能体列表吗？")) return;
    const data = await api("/api/agents/reset", {method: "POST"});
    state.agents = data.agents || [];
    state.selectedAgent = "元智能体";
    renderAgents();
    renderHeader();
}

async function refreshAgents() {
    const data = await api("/api/agents");
    state.agents = data.agents || [];
    renderAgents();
}

async function refreshSessions(render = true) {
    const data = await api("/api/sessions");
    state.sessions = data.sessions || [];
    if (render) renderSessions();
}

async function uploadFile() {
    const file = els.fileInput.files?.[0];
    if (!file || !state.session) return;
    const formData = new FormData();
    formData.append("file", file);
    formData.append("session_id", state.session.id);
    setComposerEnabled(false);
    try {
        const response = await fetch("/api/upload", {method: "POST", body: formData});
        const data = await response.json();
        if (!response.ok || !data.success) {
            throw new Error(data.error || "上传失败");
        }
        appendMessage("user", data.message.content, {markdown: false});
        await refreshSessions();
    } catch (error) {
        const node = appendMessage("assistant", "", {name: "系统", markdown: true});
        appendToolCard(node.stack, "上传失败", error.message, true);
    } finally {
        els.fileInput.value = "";
        setComposerEnabled(true);
    }
}

function updateMentionBox() {
    const value = els.input.value;
    const cursor = els.input.selectionStart;
    const at = value.lastIndexOf("@", cursor - 1);
    if (at === -1 || value.slice(at + 1, cursor).includes(" ")) {
        hideMentionBox();
        return;
    }
    const query = value.slice(at + 1, cursor);
    const matches = state.agents.filter((agent) => agent.name.includes(query)).slice(0, 8);
    replaceChildren(els.mentionBox);
    if (!matches.length) {
        hideMentionBox();
        return;
    }
    for (const agent of matches) {
        const item = document.createElement("button");
        item.type = "button";
        item.className = "mention-item";
        item.textContent = agent.name;
        item.addEventListener("click", () => {
            els.input.value = `${value.slice(0, at)}@${agent.name} ${value.slice(cursor)}`;
            els.input.focus();
            hideMentionBox();
        });
        els.mentionBox.append(item);
    }
    els.mentionBox.classList.remove("hidden");
}

function hideMentionBox() {
    els.mentionBox.classList.add("hidden");
}

function renderMarkdown(content) {
    const html = window.marked ? window.marked.parse(content || "") : escapeHtml(content || "");
    if (!window.DOMPurify) return html;
    return window.DOMPurify.sanitize(html, {
        ALLOWED_TAGS: [
            "p", "br", "strong", "em", "u", "h1", "h2", "h3", "h4", "h5", "h6",
            "ul", "ol", "li", "a", "img", "blockquote", "code", "pre", "table",
            "thead", "tbody", "tr", "th", "td", "video", "source", "audio", "hr"
        ],
        ALLOWED_ATTR: ["href", "src", "alt", "title", "controls", "type", "width", "height", "poster", "target", "rel"],
    });
}

function escapeHtml(value) {
    const div = document.createElement("div");
    div.textContent = value;
    return div.innerHTML;
}

function replaceChildren(node) {
    while (node.firstChild) node.removeChild(node.firstChild);
}

function setComposerEnabled(enabled) {
    state.streaming = !enabled;
    els.input.disabled = !enabled;
    els.send.disabled = !enabled;
    els.upload.disabled = !enabled;
}

function autoResize(textarea) {
    textarea.style.height = "auto";
    textarea.style.height = `${Math.min(textarea.scrollHeight, 160)}px`;
}

function scrollToBottom() {
    els.messages.scrollTop = els.messages.scrollHeight;
}

function initTheme() {
    const saved = localStorage.getItem("theme");
    const dark = saved ? saved === "dark" : window.matchMedia("(prefers-color-scheme: dark)").matches;
    document.documentElement.classList.toggle("dark", dark);
}

function toggleTheme() {
    const nextDark = !document.documentElement.classList.contains("dark");
    document.documentElement.classList.toggle("dark", nextDark);
    localStorage.setItem("theme", nextDark ? "dark" : "light");
}
