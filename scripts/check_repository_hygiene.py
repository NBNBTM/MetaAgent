from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

FORBIDDEN_TRACKED_EXACT = {
    ".env",
}

FORBIDDEN_TRACKED_PATTERNS = (
    "data/",
    "uploads/",
    "static/users/",
    "__pycache__",
    ".pytest_cache",
    ".venv/",
    "venv/",
    "env/",
    "user_2025",
)

SENSITIVE_PATTERNS = {
    "company/private terms": re.compile(r"unidt|UNIDT|会议室|论文|专利|数字人", re.IGNORECASE),
    "private service host": re.compile(r"service-test\.unidt|service\.unidt|ai-api\.unidt|ai-proxy\.unidt", re.IGNORECASE),
    "private IP": re.compile(r"\b(?:121\.46|180\.184)\.\d{1,3}\.\d{1,3}\b"),
    "api key shape": re.compile(r"\b(?:sk|tvly)-[A-Za-z0-9_-]{16,}\b"),
    "bearer token": re.compile(r"Bearer\s+[A-Za-z0-9._-]{16,}"),
    "disabled TLS verification": re.compile(r"verify\s*=\s*False"),
}

EMAIL_PATTERN = re.compile(
    r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
    re.IGNORECASE,
)
ALLOWED_PUBLIC_EMAILS = {"yanglinsen761@gmail.com"}

TEXT_SUFFIXES = {
    "",
    ".css",
    ".example",
    ".html",
    ".js",
    ".json",
    ".md",
    ".py",
    ".toml",
    ".txt",
    ".yml",
    ".yaml",
}

SCAN_EXCLUDES = {
    "README.md",
    "docs/images/metaagent-home.png",
    "docs/images/metaagent-chat.png",
    "docs/images/metaagent-demo.gif",
    "scripts/check_repository_hygiene.py",
}

REQUIRED_FILES = (
    "README.md",
    "License",
    ".env.example",
    ".gitignore",
    ".github/workflows/tests.yml",
    "docs/images/metaagent-demo.gif",
)


def main() -> int:
    tracked_files = run(["git", "ls-files"]).splitlines()
    failures: list[str] = []

    for file_name in tracked_files:
        normalized = file_name.replace("\\", "/")
        if normalized in FORBIDDEN_TRACKED_EXACT:
            failures.append(f"forbidden tracked path: {file_name}")
        for pattern in FORBIDDEN_TRACKED_PATTERNS:
            if normalized == pattern.rstrip("/") or pattern in normalized:
                failures.append(f"forbidden tracked path: {file_name}")

    for required in REQUIRED_FILES:
        if required not in tracked_files:
            failures.append(f"required file is not tracked: {required}")

    for file_name in tracked_files:
        if file_name in SCAN_EXCLUDES:
            continue
        path = ROOT / file_name
        if path.suffix not in TEXT_SUFFIXES or not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for label, pattern in SENSITIVE_PATTERNS.items():
            if pattern.search(text):
                failures.append(f"{label} matched in {file_name}")

    for file_name in tracked_files:
        if file_name == "scripts/check_repository_hygiene.py":
            continue
        path = ROOT / file_name
        if path.suffix not in TEXT_SUFFIXES or not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for email in EMAIL_PATTERN.findall(text):
            if email.lower() not in ALLOWED_PUBLIC_EMAILS:
                failures.append(f"third-party email matched in {file_name}")

    if failures:
        print("Repository hygiene check failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Repository hygiene check passed.")
    return 0


def run(command: list[str]) -> str:
    return subprocess.check_output(command, cwd=ROOT, text=True)


if __name__ == "__main__":
    sys.exit(main())
