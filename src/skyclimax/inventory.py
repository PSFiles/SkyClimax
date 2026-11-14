"""Filesystem inventory and magic-based classification.

Produces a stable JSON document describing every file in an extracted package:
size, SHA-256, and a ``kind`` derived from the leading bytes rather than from
the extension, so renamed payloads are still classified correctly.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

#: (magic prefix, kind) probes, evaluated in order.
MAGIC_PROBES: tuple[tuple[bytes, str], ...] = (
    (b"\x7fELF", "elf"),
    (b"SCE\x00", "self"),
    (b"\x7fPKG", "pkg"),
    (b"PSAR", "psarc"),
    (b"FArc", "farc"),
    (b"FArC", "farc"),
    (b"\x00PSF", "param_sfo"),
    (b"PNG\r\n", "png"),
    (b"\x1f\x8b", "gzip"),
    (b"ADX", "adx"),
    (b"\x80\x00", "adx"),
    (b"AFS\x00", "afs"),
    (b"TRP\x00", "trophy"),
    (b"NPD\x00", "edat"),
)


@dataclass
class FileRecord:
    relative_path: str
    size: int
    sha256: str
    kind: str
    magic: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.relative_path,
            "size": self.size,
            "sha256": self.sha256,
            "kind": self.kind,
            "magic": self.magic,
        }


@dataclass
class Inventory:
    root: Path
    files: list[FileRecord] = field(default_factory=list)

    @property
    def total_bytes(self) -> int:
        return sum(f.size for f in self.files)

    def by_kind(self) -> dict[str, dict[str, int]]:
        counts: Counter[str] = Counter()
        sizes: Counter[str] = Counter()
        for f in self.files:
            counts[f.kind] += 1
            sizes[f.kind] += f.size
        return {kind: {"count": counts[kind], "bytes": sizes[kind]} for kind in sorted(counts)}

    def to_dict(self) -> dict[str, Any]:
        return {
            "root": str(self.root),
            "file_count": len(self.files),
            "total_bytes": self.total_bytes,
            "by_kind": self.by_kind(),
            "files": [f.to_dict() for f in self.files],
        }


def classify(prefix: bytes) -> tuple[str, str]:
    for magic, kind in MAGIC_PROBES:
        if prefix.startswith(magic):
            return kind, prefix[:8].hex()
    return "unknown", prefix[:8].hex()


def hash_file(path: Path, chunk: int = 1 << 20) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        while True:
            block = fh.read(chunk)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def build_inventory(root: str | Path, patterns: Iterable[str] = ("*",)) -> Inventory:
    root = Path(root)
    inv = Inventory(root=root)
    seen: set[Path] = set()
    for pattern in patterns:
        for path in sorted(root.rglob(pattern)):
            if not path.is_file() or path in seen:
                continue
            seen.add(path)
            with path.open("rb") as fh:
                prefix = fh.read(16)
            kind, magic = classify(prefix)
            inv.files.append(
                FileRecord(
                    relative_path=path.relative_to(root).as_posix(),
                    size=path.stat().st_size,
                    sha256=hash_file(path),
                    kind=kind,
                    magic=magic,
                )
            )
    return inv


def write_json(document: dict[str, Any], destination: str | Path) -> Path:
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(document, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    return destination
