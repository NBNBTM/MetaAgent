# Contributing

MetaAgent is maintained as a portfolio project. Contributions should keep the public version reproducible, local-first, and safe to publish.

## Local Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python app.py
```

## Development Checks

Run these before opening a pull request:

```bash
pytest
python scripts/check_repository_hygiene.py
```

## Public Repository Rules

- Do not commit `.env`, API keys, local runtime data, uploaded files, cache directories, or database files.
- Keep private/company-specific services out of the public tool catalog.
- Add tests when changing routing, storage, upload handling, or MCP tool behavior.
- Keep README screenshots and GIFs generated from clean demo data only.
