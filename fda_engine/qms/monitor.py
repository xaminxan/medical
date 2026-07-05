"""QMS document monitor — watch for changes in QMS files."""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from loguru import logger


class QMSMonitor:
    """Monitor QMS documents for changes using file hashing."""

    def __init__(self, qms_path: str = "~/.fda_engine/qms"):
        self.qms_path = Path(qms_path).expanduser()
        self._hash_store: dict[str, str] = {}
        self._initialized = False

    def initialize(self):
        """Initialize the monitor by scanning existing files."""
        if self._initialized:
            return

        self.qms_path.mkdir(parents=True, exist_ok=True)

        for f in self.qms_path.rglob("*"):
            if f.is_file():
                self._hash_store[str(f)] = self._file_hash(f)

        self._initialized = True
        logger.info(f"QMS monitor initialized: {len(self._hash_store)} files tracked")

    def check_for_changes(self) -> list[dict[str, Any]]:
        """Check for new, modified, or deleted files.

        Returns:
            List of change events.
        """
        if not self._initialized:
            self.initialize()

        changes = []
        current_files = {}

        for f in self.qms_path.rglob("*"):
            if not f.is_file():
                continue

            path_str = str(f)
            current_files[path_str] = self._file_hash(f)

        # Check for new and modified files
        for path, hash_val in current_files.items():
            if path not in self._hash_store:
                changes.append({
                    "type": "added",
                    "path": path,
                    "hash": hash_val,
                })
            elif self._hash_store[path] != hash_val:
                changes.append({
                    "type": "modified",
                    "path": path,
                    "old_hash": self._hash_store[path],
                    "new_hash": hash_val,
                })

        # Check for deleted files
        for path in self._hash_store:
            if path not in current_files:
                changes.append({
                    "type": "deleted",
                    "path": path,
                })

        # Update hash store
        self._hash_store = current_files

        if changes:
            logger.info(f"QMS changes detected: {len(changes)} files")

        return changes

    def get_file_content(self, path: str) -> str | None:
        """Read a QMS file's content."""
        file_path = Path(path)
        if file_path.exists() and file_path.is_file():
            return file_path.read_text(encoding="utf-8", errors="ignore")
        return None

    def list_files(self) -> list[str]:
        """List all tracked QMS files."""
        return list(self._hash_store.keys())

    def _file_hash(self, path: Path) -> str:
        """Compute SHA-256 hash of a file."""
        sha256 = hashlib.sha256()
        try:
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except Exception:
            return ""
