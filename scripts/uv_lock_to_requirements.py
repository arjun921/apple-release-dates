"""Convert `uv.lock` (TOML) into a pinned requirements file.

This script reads the `uv.lock` file in the repository root and writes
`scripts/requirements-pinned.txt` containing `name==version` lines for
all non-virtual packages. It intentionally skips the package whose
source.virtual is '.' or which matches the project name.

Usage:
    python scripts/uv_lock_to_requirements.py

This is intended for CI where pip doesn't understand `uv.lock` natively.
"""

from __future__ import annotations

import tomllib
from pathlib import Path
import sys


def main(
    lock_path: Path = Path("uv.lock"),
    out_path: Path = Path("scripts/requirements-pinned.txt"),
) -> int:
    if not lock_path.exists():
        print(f"Lock file not found: {lock_path}")
        return 2

    data = tomllib.loads(lock_path.read_text(encoding="utf-8"))

    packages = data.get("package", [])
    if not packages:
        print("No packages found in lockfile")
        return 3

    lines = []
    seen = set()
    for pkg in packages:
        name = pkg.get("name")
        version = pkg.get("version")
        source = pkg.get("source", {}) or {}

        # Skip the virtual/project package (source.virtual == '.')
        if source.get("virtual") == ".":
            continue

        # Some lock formats include the project itself; skip if name matches repo
        if name.lower() == "apple-release-dates":
            continue

        if not name or not version:
            continue

        key = name.lower()
        if key in seen:
            continue
        seen.add(key)

        lines.append(f"{name}=={version}")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {len(lines)} pinned requirements to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
