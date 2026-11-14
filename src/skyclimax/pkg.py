"""PlayStation 3 ``.pkg`` header reader.

Only the plaintext 0xC0-byte header is parsed. Entry enumeration requires the
package body, which is encrypted with the public ``PS3_GPKG`` AES-CTR key; that
step is delegated to the vendored ps3recomp extractor (see
``docs/en-US/build/environment.md``) instead of being reimplemented here.

Verified against ``UP0177-NPUB30151_00-AFTERBURNERCMX00.pkg``:

* ``total_size`` equals the file size on disk (551,772,592 bytes);
* ``item_count`` equals the number of files the extractor reports (46);
* ``content_id`` matches the file name.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PKG_MAGIC = b"\x7fPKG"


@dataclass
class PkgHeader:
    path: Path
    file_size: int
    revision: int
    info_offset: int
    info_size: int
    header_size: int
    item_count: int
    total_size: int
    data_offset: int
    data_size: int
    content_id: str
    digest: bytes
    data_iv: bytes

    @property
    def content_id_tail(self) -> str:
        """The part of the content ID after the two underscores (the title key name)."""
        parts = self.content_id.split("_")
        return parts[-1] if parts else self.content_id

    @property
    def size_matches_file(self) -> bool:
        """``total_size`` in the header must agree with the file on disk."""
        return self.total_size == self.file_size

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": str(self.path),
            "file_size": self.file_size,
            "revision": f"0x{self.revision:08x}",
            "info_offset": self.info_offset,
            "info_size": self.info_size,
            "header_size": self.header_size,
            "item_count": self.item_count,
            "total_size": self.total_size,
            "data_offset": self.data_offset,
            "data_size": self.data_size,
            "content_id": self.content_id,
            "digest": self.digest.hex(),
            "data_iv": self.data_iv.hex(),
            "size_matches_file": self.total_size == self.file_size,
        }


def parse_pkg_header(path: str | Path) -> PkgHeader:
    path = Path(path)
    file_size = path.stat().st_size
    with path.open("rb") as fh:
        raw = fh.read(0xC0)
    if raw[:4] != PKG_MAGIC:
        raise ValueError(f"{path}: not a PS3 package (magic {raw[:4]!r})")
    revision = struct.unpack(">I", raw[4:8])[0]
    info_offset, info_size, header_size, item_count = struct.unpack(">IIII", raw[8:24])
    total_size, = struct.unpack(">Q", raw[24:32])
    data_offset, data_size = struct.unpack(">QQ", raw[32:48])
    content_id = raw[0x30:0x60].split(b"\x00", 1)[0].decode("ascii", "replace")
    return PkgHeader(
        path=path,
        file_size=file_size,
        revision=revision,
        info_offset=info_offset,
        info_size=info_size,
        header_size=header_size,
        item_count=item_count,
        total_size=total_size,
        data_offset=data_offset,
        data_size=data_size,
        content_id=content_id,
        digest=raw[0x60:0x70],
        data_iv=raw[0x70:0x80],
    )
