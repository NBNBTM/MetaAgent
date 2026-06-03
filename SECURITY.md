# Security Policy

## Supported Version

This repository is a local-first portfolio project. The public `main` branch is the supported version.

## Reporting Issues

Please open a GitHub issue for security-relevant problems that do not expose secrets. If a report includes credentials, private data, or exploit details, contact the repository owner privately instead of posting them publicly.

## Secret Handling

- The project does not ship with a model key.
- Users configure their own key in `.env`.
- `.env`, runtime databases, uploads, caches, and local user data are ignored by Git.
- Any API key that was previously committed anywhere should be treated as exposed and rotated outside this repository.

## Local Data

By default, MetaAgent stores local runtime data under `data/`:

- `data/metaagent.sqlite3`
- `data/uploads/`

These files are local development artifacts and should not be uploaded to GitHub.
