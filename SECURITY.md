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

## Outbound Network Requests

The `get_internet_time` MCP tool only accepts its documented HTTPS server allowlist, does not follow redirects, and rejects local, private, metadata-service, file, and arbitrary external URLs before making a request.

## Browser Data Isolation

- Chat input is sent in a POST body so prompts are not placed in request URLs.
- Browser identity is stored in Quart's signed session cookie, and uploaded files can only be retrieved by the signed-in browser session that owns them.
- Assistant Markdown is rendered only when both Marked and DOMPurify are available; otherwise it falls back to escaped plain text.
- This remains a local-first portfolio application without a production authentication system. Do not expose it as a multi-user public service without adding real authentication, authorization, rate limiting, and deployment-specific secret management.
