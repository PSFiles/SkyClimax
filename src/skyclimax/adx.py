"""CRI ADX audio header reader.

ADX is the CRI Middleware stream format used for every music and voice asset in
this title (``USRDIR/rom/adx``). Only the fixed header is parsed; the coded
audio payload is not decoded.

======== =====================================================
0x00     ``u16`` 0x8000 signature
0x02     ``u16`` offset of the ``(c)CRI`` string
0x04     ``u8``  encoding (3 = 4-bit, version 3)
0x05     ``u8``  block size
0x06     ``u8``  sample bit depth
0x07     ``u8``  channel count
0x08     ``u32`` sample rate
0x0C     ``u32`` total samples
0x10     ``u16`` high-pass frequency
0x12     ``u8``  version
0x13     ``u8``  flags (bit 0 = loop enabled)
======== =====================================================

When the loop flag is set, four ``u32`` follow at 0x14: loop start sample,
loop start byte, loop end sample, loop end byte.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ADX_SIGNATURE = 0x8000


@dataclass
class AdxHeader:
    path: Path
    file_size: int
    copyright_offset: int
    encoding: int
    block_size: int
    bit_depth: int
    channels: int
    sample_rate: int
    sample_count: int
    highpass: int
    version: int
    flags: int
    loop: dict[str, int] | None

    @property
    def duration_seconds(self) -> float:
        if not self.sample_rate:
            return 0.0
        return self.sample_count / self.sample_rate

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": str(self.path),
            "file_size": self.file_size,
            "encoding": self.encoding,
            "block_size": self.block_size,
            "bit_depth": self.bit_depth,
            "channels": self.channels,
            "sample_rate": self.sample_rate,
            "sample_count": self.sample_count,
            "duration_seconds": round(self.duration_seconds, 3),
            "highpass": self.highpass,
            "version": self.version,
            "flags": self.flags,
            "loop": self.loop,
        }


def parse_adx(path: str | Path) -> AdxHeader:
    path = Path(path)
    raw = path.read_bytes()
    if len(raw) < 0x14:
        raise ValueError(f"{path}: too small to be ADX ({len(raw)} bytes)")
    signature = struct.unpack(">H", raw[0:2])[0]
    if signature != ADX_SIGNATURE:
        raise ValueError(f"{path}: unexpected ADX signature 0x{signature:04x}")

    copyright_offset, = struct.unpack(">H", raw[2:4])
    encoding, block_size, bit_depth, channels = raw[4], raw[5], raw[6], raw[7]
    sample_rate, sample_count = struct.unpack(">II", raw[8:16])
    highpass = struct.unpack(">H", raw[16:18])[0]
    version, flags = raw[18], raw[19]

    loop = None
    if flags & 0x01 and len(raw) >= 0x28:
        start_sample, start_byte, end_sample, end_byte = struct.unpack(">IIII", raw[0x14:0x24])
        loop = {
            "start_sample": start_sample,
            "start_byte": start_byte,
            "end_sample": end_sample,
            "end_byte": end_byte,
        }

    return AdxHeader(
        path=path,
        file_size=len(raw),
        copyright_offset=copyright_offset,
        encoding=encoding,
        block_size=block_size,
        bit_depth=bit_depth,
        channels=channels,
        sample_rate=sample_rate,
        sample_count=sample_count,
        highpass=highpass,
        version=version,
        flags=flags,
        loop=loop,
    )
