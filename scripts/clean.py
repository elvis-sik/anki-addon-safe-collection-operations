"""Remove generated project output."""

from __future__ import annotations

import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    for path in (ROOT / "dist", ROOT / ".mypy_cache", ROOT / ".ruff_cache"):
        shutil.rmtree(path, ignore_errors=True)
    for path in ROOT.rglob("__pycache__"):
        shutil.rmtree(path, ignore_errors=True)


if __name__ == "__main__":
    main()
