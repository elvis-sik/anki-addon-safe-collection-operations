"""Fail when public source contains private-machine or credential material."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
IGNORED_PARTS = {".git", ".mypy_cache", ".ruff_cache", "__pycache__", "dist"}
TEXT_SUFFIXES = {"", ".json", ".md", ".py", ".toml", ".txt", ".yml", ".yaml"}
FORBIDDEN = {
    "absolute home path": re.compile(r"/(?:Users|home)/[A-Za-z0-9._-]+/"),
    "1Password reference": re.compile(r"op://"),
    "private IPv4 address": re.compile(
        r"\b(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}|"
        r"192\.168\.\d{1,3}\.\d{1,3}|"
        r"172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})\b"
    ),
    "PEM private key": re.compile(r"BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY"),
}


def checked_files() -> list[Path]:
    return [
        path
        for path in ROOT.rglob("*")
        if path.is_file()
        and not any(part in IGNORED_PARTS for part in path.relative_to(ROOT).parts)
        and path.suffix.lower() in TEXT_SUFFIXES
    ]


def main() -> None:
    violations: list[str] = []
    for path in checked_files():
        if path == Path(__file__).resolve():
            continue
        text = path.read_text(encoding="utf-8")
        for label, pattern in FORBIDDEN.items():
            if pattern.search(text):
                violations.append(f"{path.relative_to(ROOT)}: {label}")
    if violations:
        raise SystemExit("public-data scan failed:\n" + "\n".join(violations))
    print(f"public-data scan passed ({len(checked_files())} text files)")


if __name__ == "__main__":
    main()
