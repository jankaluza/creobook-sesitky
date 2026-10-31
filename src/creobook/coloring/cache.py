"""Persistent illustration files. Writes are atomic so a crash cannot leave a half PNG."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def atomic_write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".partial")
    temporary.write_bytes(data)
    os.replace(temporary, path)


def atomic_write_text(path: Path, text: str) -> None:
    atomic_write_bytes(path, text.encode("utf-8"))


def atomic_write_json(path: Path, payload: Any) -> None:
    atomic_write_text(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def illustration_dir(root: Path, index: int, illustration_id: str) -> Path:
    return root / "illustrations" / f"{index:02d}-{illustration_id}"


def read_meta(directory: Path) -> dict[str, Any] | None:
    path = directory / "meta.json"
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))
