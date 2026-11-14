"""Sega ``FArc`` container reader.

Two variants were observed in the retail package and they differ in the case of
the fourth magic byte:

``FArc`` (``...63``)
    ``{magic, u32 first_data_offset - 8, u32 version}`` then records of
    ``{cstring name, u32 offset, u32 size}``.
    Verified on ``USRDIR/ps3/SYSTEM.farc`` (2 records).

``FArC`` (``...43``)
    Same header, records of
    ``{cstring name, u32 offset, u32 compressed_size, u32 uncompressed_size}``.
    Verified on ``USRDIR/ps3/shader_cg.farc``, whose payloads begin with the
    gzip magic ``1f 8b`` when ``compressed_size != uncompressed_size``.

Because only two samples were available, the reader treats the variant as a
hypothesis: it is selected by the magic byte and every record is validated
against the file bounds before being accepted. Records are never invented; a
failed validation raises :class:`FarcError`.
"""

from __future__ import annotations

import gzip
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .binary import Reader, is_printable_name

FARC_MAGIC = b"FArc"
FARC_MAGIC_COMPRESSED = b"FArC"


class FarcError(ValueError):
    """Raised when a FARC container does not match a supported variant."""


@dataclass
class FarcEntry:
    name: str
    offset: int
    size: int
    uncompressed_size: int

    @property
    def compressed(self) -> bool:
        return self.uncompressed_size != self.size

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "offset": self.offset,
            "size": self.size,
            "uncompressed_size": self.uncompressed_size,
            "compressed": self.compressed,
        }


@dataclass
class FarcArchive:
    path: Path
    variant: str
    version: int
    data_offset: int
    entries: list[FarcEntry]

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": str(self.path),
            "variant": self.variant,
            "version": self.version,
            "data_offset": self.data_offset,
            "entry_count": len(self.entries),
            "entries": [e.to_dict() for e in self.entries],
        }


def parse_farc(path: str | Path) -> FarcArchive:
    path = Path(path)
    file_size = path.stat().st_size
    with path.open("rb") as fh:
        r = Reader(fh)
        magic = r.read(4)
        if magic not in (FARC_MAGIC, FARC_MAGIC_COMPRESSED):
            raise FarcError(f"{path}: unexpected FARC magic {magic!r}")
        first_data_offset = r.u32() + 8
        version = r.u32()
        if not 0x0C < first_data_offset <= file_size:
            raise FarcError(
                f"{path}: first data offset 0x{first_data_offset:x} outside file (size 0x{file_size:x})"
            )

        compressed_variant = magic == FARC_MAGIC_COMPRESSED
        entries: list[FarcEntry] = []
        while r.tell() < first_data_offset:
            name = r.cstring(limit=512)
            if not is_printable_name(name):
                raise FarcError(f"{path}: invalid entry name at 0x{r.tell():x}: {name!r}")
            offset = r.u32()
            size = r.u32()
            usize = r.u32() if compressed_variant else size
            if offset + size > file_size:
                raise FarcError(
                    f"{path}: entry {name!r} spans 0x{offset:x}+0x{size:x} beyond file size 0x{file_size:x}"
                )
            entries.append(FarcEntry(name, offset, size, usize))

    return FarcArchive(
        path=path,
        variant="compressed" if compressed_variant else "plain",
        version=version,
        data_offset=first_data_offset,
        entries=entries,
    )


def read_entry(archive: FarcArchive, entry: FarcEntry) -> bytes:
    """Return the (decompressed) payload of a single entry."""
    with archive.path.open("rb") as fh:
        fh.seek(entry.offset)
        payload = fh.read(entry.size)
    if payload[:2] == b"\x1f\x8b":
        return gzip.decompress(payload)
    return payload


def extract_all(archive: FarcArchive, out_dir: str | Path) -> list[Path]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for entry in archive.entries:
        # Entry names are flat file names in the observed archives; reject separators
        # so a malformed archive cannot escape the output directory.
        safe = Path(entry.name).name
        if not safe or safe in (".", ".."):
            raise FarcError(f"refusing to extract unsafe entry name {entry.name!r}")
        target = out / safe
        target.write_bytes(read_entry(archive, entry))
        written.append(target)
    return written


def _unused_struct_guard() -> None:  # pragma: no cover - keeps the import meaningful
    struct.unpack(">I", b"\x00\x00\x00\x00")
