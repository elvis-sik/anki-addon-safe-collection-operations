"""Build a deterministic Anki add-on archive."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
ARCHIVE = DIST / "anki-addon-safe-collection-operations.ankiaddon"
TOP_LEVEL_FILES = (
    "__init__.py",
    "config.json",
    "config.md",
    "LICENSE",
    "manifest.json",
    "README.md",
)


def source_files() -> list[tuple[Path, str]]:
    files = [(ROOT / name, name) for name in TOP_LEVEL_FILES]
    package = ROOT / "safe_collection_operations"
    files.extend(
        (path, path.relative_to(ROOT).as_posix())
        for path in package.rglob("*.py")
        if "__pycache__" not in path.parts
    )
    return sorted(files, key=lambda item: item[1])


def main() -> None:
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    if manifest["package"] != "anki_addon_safe_collection_operations":
        raise SystemExit("manifest package does not match the public package name")
    DIST.mkdir(exist_ok=True)
    with zipfile.ZipFile(ARCHIVE, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path, archive_name in source_files():
            info = zipfile.ZipInfo(archive_name, date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, path.read_bytes())
    print(ARCHIVE.relative_to(ROOT))


if __name__ == "__main__":
    main()
