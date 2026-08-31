FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN groupadd --system metaagent \
    && useradd --system --gid metaagent --create-home metaagent

COPY pyproject.toml README.md License ./
COPY app.py agents.json meta.json mcp_server_config.json ./
COPY meta_agent_app ./meta_agent_app
COPY mcp ./mcp
COPY prompt ./prompt
COPY static ./static
COPY templates ./templates

RUN python -m pip install --upgrade pip \
    && python -m pip install .

RUN mkdir -p /app/data \
    && chown -R metaagent:metaagent /app

USER metaagent

EXPOSE 18899

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:18899/', timeout=5)"

CMD ["hypercorn", "app:app", "--bind", "0.0.0.0:18899"]
