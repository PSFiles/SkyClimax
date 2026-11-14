"""Big-endian reader helpers shared by the container parsers."""

from __future__ import annotations

import struct
from typing import BinaryIO


class Reader:
    """Sequential big-endian reader over a binary stream."""

    def __init__(self, fh: BinaryIO) -> None:
        self.fh = fh

    def tell(self) -> int:
        return self.fh.tell()

    def seek(self, offset: int) -> None:
        self.fh.seek(offset)

    def read(self, n: int) -> bytes:
        data = self.fh.read(n)
        if len(data) != n:
            raise EOFError(f"wanted {n} bytes at 0x{self.fh.tell() - len(data):x}, got {len(data)}")
        return data

    def u8(self) -> int:
        return self.read(1)[0]

    def u16(self) -> int:
        return struct.unpack(">H", self.read(2))[0]

    def u32(self) -> int:
        return struct.unpack(">I", self.read(4))[0]

    def u64(self) -> int:
        return struct.unpack(">Q", self.read(8))[0]

    def cstring(self, limit: int = 4096) -> str:
        """Read a NUL-terminated ASCII string."""
        out = bytearray()
        while len(out) < limit:
            b = self.read(1)[0]
            if b == 0:
                return out.decode("ascii", "replace")
            out.append(b)
        raise ValueError("unterminated string")


def is_printable_name(name: str) -> bool:
    """Container entry names in this package are plain ASCII path fragments."""
    if not name or len(name) > 512:
        return False
    return all(0x20 <= ord(ch) < 0x7F for ch in name)
