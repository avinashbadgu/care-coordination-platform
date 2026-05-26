"""Local-filesystem object storage for uploaded files.

Deliberately simple — files live under STORAGE_DIR/{patient_id}/{kind}/{uuid}_{name}.
Swap with S3 / Azure Blob later by replacing FileStorage; the service
layer only depends on `save_bytes()` returning a storage path.
"""
from __future__ import annotations

import re
import uuid
from pathlib import Path

from app.core.config import get_settings

_SAFE_NAME_RE = re.compile(r"[^A-Za-z0-9._-]+")


def _safe_filename(name: str) -> str:
    base = _SAFE_NAME_RE.sub("_", name).strip("._-")
    return base[:120] or "file"


class FileStorage:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or get_settings().storage_dir

    def save_bytes(
        self, *, patient_id: int, kind: str, filename: str, data: bytes
    ) -> str:
        folder = self.root / str(patient_id) / kind
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"{uuid.uuid4().hex}_{_safe_filename(filename)}"
        path.write_bytes(data)
        return str(path)

    def read_bytes(self, storage_path: str) -> bytes:
        return Path(storage_path).read_bytes()


def get_storage() -> FileStorage:
    return FileStorage()
