"""Sony ``PSARC`` archive header reader.

The header parses cleanly for ``USRDIR/ps3/rom.psarc``, but the table of
contents does not follow the published layout: no ASCII entry names and no
deflate stream exist anywhere in the header span, and the region has an entropy
of ~7.2 bits/byte. :func:`parse_psarc` therefore reports ``toc_state`` as
``"opaque"`` instead of inventing entries.

Callers must treat ``entries`` as authoritative only when ``toc_state`` is
``"parsed"``.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

PSARC_MAGIC = b"PSAR"
PSARC_HEADER_SIZE = 0x100


@dataclass
class PsarcHeader:
    path: Path
    file_size: int
    version: int
    compression: str
    header_span: int
    toc_entry_size: int
    toc_entry_count: int
    block_size: int
    flags: int
    toc_state: str = "unread"
    toc_reason: str = ""
    entries: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": str(self.path),
            "file_size": self.file_size,
            "version": f"0x{self.version:08x}",
            "compression": self.compression,
            "header_span": self.header_span,
            "toc_entry_size": self.toc_entry_size,
            "toc_entry_count": self.toc_entry_count,
            "block_size": self.block_size,
            "flags": self.flags,
            "toc_state": self.toc_state,
            "toc_reason": self.toc_reason,
            "entry_count": len(self.entries),
            "entries": self.entries,
        }


def parse_psarc(path: str | Path, probe_entries: int = 32) -> PsarcHeader:
    path = Path(path)
    file_size = path.stat().st_size
    with path.open("rb") as fh:
        head = fh.read(PSARC_HEADER_SIZE)
        if head[:4] != PSARC_MAGIC:
            raise ValueError(f"{path}: not a PSARC (magic {head[:4]!r})")
        version, = struct.unpack(">I", head[4:8])
        compression = head[8:12].decode("ascii", "replace")
        header_span, toc_entry_size, toc_entry_count, block_size, flags = struct.unpack(
            ">IIIII", head[12:32]
        )
        hdr = PsarcHeader(
            path=path,
            file_size=file_size,
            version=version,
            compression=compression,
            header_span=header_span,
            toc_entry_size=toc_entry_size,
            toc_entry_count=toc_entry_count,
            block_size=block_size or 0x10000,
            flags=flags,
        )

        # Validate the documented TOC layout before trusting it.
        fh.seek(PSARC_HEADER_SIZE)
        toc = fh.read(min(toc_entry_size * min(toc_entry_count, probe_entries), 1 << 20))
        plausible = 0
        checked = 0
        max_block = max(1, file_size // hdr.block_size + 1)
        for i in range(0, len(toc) - toc_entry_size + 1, toc_entry_size):
            entry = toc[i : i + toc_entry_size]
            _md5 = entry[:16]
            block_index, size, offset = struct.unpack(">III", entry[16:28])
            checked += 1
            if block_index < max_block and offset < hdr.block_size and size < file_size:
                plausible += 1
        if checked == 0:
            hdr.toc_state = "unread"
            hdr.toc_reason = "table of contents lies outside the file"
        elif plausible == checked:
            hdr.toc_state = "parsed"
        else:
            hdr.toc_state = "opaque"
            hdr.toc_reason = (
                f"only {plausible}/{checked} probed TOC entries match the documented layout "
                f"(block_size={hdr.block_size}, file_size={file_size}); the table is treated "
                "as unreadable rather than guessed"
            )
    return hdr
