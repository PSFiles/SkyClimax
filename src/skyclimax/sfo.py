"""PARAM.SFO reader (PlayStation 3 system metadata).

Layout (little-endian):

===== ==============================================
0x000 ``\\0PSF`` magic
0x004 ``u32`` version (0x00000101 observed)
0x008 ``u32`` key-table offset
0x00C ``u32`` data-table offset
0x010 ``u32`` entry count
0x014 index entries, 16 bytes each
===== ==============================================

Each index entry is ``{u16 key_offset, u16 format, u32 length, u32 max_length,
u32 data_offset}``; ``key_offset`` is relative to the key table and
``data_offset`` relative to the data table. ``format`` 0x0204 is UTF-8 string,
0x0404 is ``u32``.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SFO_MAGIC = b"\x00PSF"
FMT_UTF8 = 0x0204
FMT_U32 = 0x0404


@dataclass
class SfoEntry:
    key: str
    fmt: int
    raw: bytes

    @property
    def value(self) -> Any:
        if self.fmt == FMT_UTF8:
            return self.raw.split(b"\x00", 1)[0].decode("utf-8", "replace")
        if self.fmt == FMT_U32 and len(self.raw) >= 4:
            return struct.unpack("<I", self.raw[:4])[0]
        return self.raw


def parse_sfo(path: str | Path) -> dict[str, SfoEntry]:
    raw = Path(path).read_bytes()
    if raw[:4] != SFO_MAGIC:
        raise ValueError(f"{path}: not a PARAM.SFO (magic {raw[:4]!r})")
    _version, key_tab, data_tab, count = struct.unpack("<IIII", raw[4:20])
    entries: dict[str, SfoEntry] = {}
    for i in range(count):
        base = 20 + i * 16
        key_off, fmt, length, _max_len, data_off = struct.unpack("<HHIII", raw[base : base + 16])
        key_start = key_tab + key_off
        key_end = raw.index(b"\x00", key_start)
        key = raw[key_start:key_end].decode("ascii", "replace")
        entries[key] = SfoEntry(key, fmt, raw[data_tab + data_off : data_tab + data_off + length])
    return entries


def sfo_summary(path: str | Path) -> dict[str, Any]:
    entries = parse_sfo(path)
    out: dict[str, Any] = {"path": str(path), "entry_count": len(entries), "fields": {}}
    for key, entry in entries.items():
        value = entry.value
        if isinstance(value, bytes):
            value = {"bytes": len(value), "hex": value[:32].hex()}
        out["fields"][key] = value
    return out
