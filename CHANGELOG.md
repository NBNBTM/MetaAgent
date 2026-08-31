# Changelog

All notable changes to MetaAgent are documented in this file. The project follows semantic versioning while it evolves toward a stable 1.0 release.

## [0.2.0] - 2026-08-31

### Added

- CodeQL analysis for Python and JavaScript.
- Restored and tested public internet-time and data-visualization MCP tools.
- Python 3.11 and 3.12 CI coverage with editable-install validation.
- Docker and Docker Compose launch paths with non-root execution and persistent local data.
- Structured issue templates, a pull request template, and repository ownership metadata.
- Playwright end-to-end coverage for chat, responsive navigation, theme state, and browser console errors.
- Explicit public contribution boundaries and third-party notices.

### Changed

- Updated GitHub Actions to the current major versions.
- Repaired setuptools package discovery and modernized MIT license metadata.
- Strengthened MCP shutdown handling and repository hygiene checks.
- Restricted the internet-time tool to approved public servers to prevent internal-network requests.
- Moved chat prompts from URL query parameters to POST request bodies.
- Enforced per-browser ownership checks when serving uploaded files.
- Replaced the unsigned user identifier cookie with Quart's signed session cookie.
- Made Markdown rendering fail closed to escaped text when sanitization is unavailable.
- Added an explicit application favicon to keep browser sessions free of missing-asset errors.
- Removed the empty-state prompt as soon as the first chat message is rendered.
- Replaced historical avatar assets with a generic public-safe user avatar.

### Removed

- Obsolete example files, legacy helper modules, and unused third-party tool modules.
- Stale employer terminology and private legacy markers from public repository content.

## [0.1.1] - 2026-06-03

- Replaced static README screenshots with an animated demo GIF.
- Added Dependabot, security guidance, contribution guidance, editor defaults, and portfolio checks.
- Updated GitHub Actions dependencies and repository hygiene validation.

## [0.1.0] - 2026-06-03

- Published the initial public portfolio edition.
- Added meta-agent routing, MCP tools, the streaming Quart UI, and SQLite-backed sessions.
- Established the public-safe `.env.example` and ignored local runtime data.

[0.2.0]: https://github.com/NBNBTM/MetaAgent/compare/v0.1.1...v0.2.0
[0.1.1]: https://github.com/NBNBTM/MetaAgent/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/NBNBTM/MetaAgent/releases/tag/v0.1.0
