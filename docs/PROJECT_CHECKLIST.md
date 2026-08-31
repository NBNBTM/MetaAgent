# Portfolio Readiness Checklist

This checklist documents the public-version boundaries for MetaAgent.

## Runtime Configuration

- Model access is configured by the user through `.env`.
- No model weights or API keys are bundled with the repository.
- Without `OPENAI_API_KEY`, the app still demonstrates local meta-agent routing through a keyword-based fallback.
- `OPENAI_BASE_URL` supports OpenAI-compatible endpoints.
- `SECRET_KEY` is local-demo oriented by default and should be replaced for any hosted deployment.

## Local Data Boundary

Ignored runtime paths:

- `.env`
- `data/`
- `uploads/`
- `static/users/`
- `__pycache__/`
- `.pytest_cache/`
- `.venv/`

The app stores local chat/session state in SQLite and uploaded files under the configured data directory. These files are local artifacts, not repository content.

## MCP Tool Boundary

Enabled public demo modules:

- `internet_time`
- `calculator`
- `data_analysis`
- `data_visualization`

Private, company-specific, or high-risk local filesystem tools are not enabled in the public MCP catalog.

## Repository Hygiene

Before pushing:

```bash
python -m pip install -e ".[test]"
python -m pytest
python scripts/check_repository_hygiene.py
git status --ignored --short
```

Expected result:

- tests pass;
- hygiene check passes;
- `.env` may appear as ignored;
- no runtime data or cache files are tracked.

## GitHub Configuration

Configured for the public portfolio repository:

- README demo GIF and static screenshot fallbacks;
- GitHub Actions test workflow;
- Python 3.11 and 3.12 test matrix;
- Docker image build and web-start smoke test;
- Playwright desktop/mobile browser workflow test;
- CodeQL analysis for Python and JavaScript;
- Dependabot for Python and GitHub Actions dependencies;
- MIT license;
- Security policy;
- Contribution guide;
- issue and pull request templates;
- changelog and semantic-versioned releases;
- release notes for published versions.

## Current Limitations

- This is a local-first demo, not a production multi-user SaaS deployment.
- Real LLM reasoning and live tool-calling conversations require a user-provided API key.
- Uploaded files remain on the local machine unless the user deploys the app elsewhere.
- Optional external MCP services are disabled unless explicitly configured.
- The internet-time tool only connects to its explicit public-server allowlist and does not follow redirects.
