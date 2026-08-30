# MetaAgent

[![Tests](https://github.com/NBNBTM/MetaAgent/actions/workflows/tests.yml/badge.svg)](https://github.com/NBNBTM/MetaAgent/actions/workflows/tests.yml)
[![Release](https://img.shields.io/github/v/release/NBNBTM/MetaAgent)](https://github.com/NBNBTM/MetaAgent/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](License)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB.svg)](https://www.python.org/)

MetaAgent is a portfolio-ready web chat application that demonstrates a **meta-agent + MCP tool-calling workflow**. A user describes a task, the meta-agent decides which capability group is needed, creates or selects a specialized agent, and the selected agent can call public MCP tools to complete the task.

This repository is the public version of the project. It is designed to be reproducible, safe to publish, and easy to run locally.

## Project Context and Contribution

The internship system I worked with already had its primary backend workflow. My internship contribution focused on the web experience: reorganizing the information architecture, clarifying sessions and agent state, improving streaming-response and tool-call feedback, refining upload and error interactions, supporting agent mentions, and improving responsive behavior.

After the internship, I prepared this separate public portfolio edition to demonstrate the general meta-agent and MCP interaction pattern. The public edition adds and consolidates local SQLite-backed state, public-safe tool configuration, fallback behavior, tests, documentation, demo assets, and repository hygiene checks while excluding company-specific services, credentials, runtime data, uploads, and user history. It is not a publication of the original internal system and does not imply employer endorsement.

## Demo

![MetaAgent demo](docs/images/metaagent-demo.gif)

Static fallback images are available at [`docs/images/metaagent-home.png`](docs/images/metaagent-home.png) and [`docs/images/metaagent-chat.png`](docs/images/metaagent-chat.png).

## Highlights

- **Meta-agent routing**: maps user requests to capability groups and creates task-specific agents.
- **MCP tool integration**: discovers and calls public MCP tools through a Python MCP client.
- **Streaming chat UI**: supports SSE streaming, Markdown rendering, tool-call cards, file upload UI, dark mode, and responsive layout.
- **SQLite-backed state**: stores users, sessions, messages, agents, and upload metadata in a local SQLite database.
- **Public-safe project shape**: excludes local secrets, runtime data, upload files, private services, and user history from Git.
- **Repository hygiene checks**: CI verifies tests and checks that secrets, runtime data, and private legacy markers are not tracked.

## Architecture

```mermaid
flowchart LR
    UI["Browser UI"] --> API["Quart API"]
    API --> Store["SQLite Store"]
    API --> LLM["OpenAI-compatible LLM"]
    API --> Agent["Agent Service"]
    Agent --> Catalog["Tool Catalog meta.json"]
    API --> MCP["MCP Client"]
    MCP --> Tools["Public MCP Tool Server"]
```

Core directories:

- `meta_agent_app/`: configuration, storage, LLM client, agent orchestration, MCP client, and routes.
- `mcp/server/mcp_server/`: public demo MCP tool server.
- `templates/` and `static/`: single-page web chat interface.
- `tests/`: backend and API tests.
- `scripts/`: repository hygiene and README asset generation helpers.

## What It Can Do

The public demo tool catalog includes:

- **Calculator tools**: expression evaluation, equations, derivatives, integrals, statistics, regression, and matrix operations.
- **Data analysis tools**: data quality checks, missing-value handling, standardization, classification, clustering, and dimensionality reduction.

## Model and API Key Behavior

This project does **not** include a bundled model or a bundled API key.

- If `OPENAI_API_KEY` is configured, MetaAgent uses the OpenAI-compatible endpoint and model configured in `.env`.
- If no API key is configured, the meta-agent falls back to a local keyword-based demo router. This lets the UI demonstrate agent creation, but real LLM responses and tool-calling conversations require a valid API key.
- Every user should provide their own API key locally. Never commit `.env`.

## Quick Start

Requirements:

- Python 3.11+
- Node.js only if you enable optional Node-based MCP servers

Install and run:

```bash
python --version
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env`:

```bash
OPENAI_API_KEY=your_api_key
MODEL=gpt-4o-mini
```

Start the app:

```bash
python app.py
```

Open:

```text
http://127.0.0.1:18899
```

Production-style local launch:

```bash
hypercorn app:app --bind 127.0.0.1:18899
```

## Demo Prompts

Try these prompts in the web UI:

- `Calculate the mean and standard deviation of 12, 18, 21, and 30.`
- `Solve x**2 - 5*x + 6 = 0.`
- `I uploaded a CSV file. Check its data quality and summarize missing values.`

## Environment Variables

`.env.example` contains the supported settings:

- `OPENAI_API_KEY`: your model API key.
- `OPENAI_BASE_URL`: optional OpenAI-compatible base URL.
- `MODEL`: model name, defaulting to `gpt-4o-mini`.
- `METAAGENT_DATA_DIR`: local runtime data directory, defaulting to `data/`.
- `DATABASE_PATH`: SQLite database path inside the data directory.
- `UPLOAD_DIR`: local upload directory.
- `MCP_SERVER_CONFIG_PATH`: MCP server configuration file.
- `METAAGENT_PYTHON_PATH`: optional Python interpreter path for MCP subprocesses.
- `SECRET_KEY`: local Quart session secret. Use a unique value outside local demos.
- `TAVILY_API_KEY`: optional key for the disabled-by-default Tavily MCP server.

## Local Data and Privacy

Runtime data is stored locally:

- SQLite database: `data/metaagent.sqlite3`
- Uploaded files: `data/uploads/`
- Local secrets: `.env`

These paths are ignored by Git. They are not meant to be uploaded to GitHub.

If you want to reset local state:

```bash
rm -rf data uploads
```

## Tests

Run:

```bash
pytest
```

Repository hygiene checks:

```bash
python scripts/check_repository_hygiene.py
```

Regenerate the README GIF after updating screenshots:

```bash
pip install -e ".[docs]"
python scripts/generate_readme_gif.py
```

The GIF should always be generated from clean demo data, never from personal chat history.

## Repository Configuration

This project includes the public repository basics expected for a portfolio project:

- GitHub Actions test workflow: `.github/workflows/tests.yml`
- Dependabot update checks: `.github/dependabot.yml`
- Repository hygiene script: `scripts/check_repository_hygiene.py`
- Public contribution guidance: `CONTRIBUTING.md`
- Security and secret-handling notes: `SECURITY.md`
- Editor defaults: `.editorconfig`
- Portfolio readiness checklist: `docs/PROJECT_CHECKLIST.md`

## Portfolio Notes

This public version focuses on the core engineering story:

- decomposing a large single-file prototype into service-oriented backend modules;
- replacing mixed JSON/localStorage state with SQLite-backed server state;
- integrating MCP tool discovery and tool calls with a streaming LLM chat flow;
- rebuilding the web UI for a cleaner session, agent, upload, and mobile experience;
- preparing the repository for safe public sharing.

## License

MIT License.
