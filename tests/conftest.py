"""Builders for synthetic fixtures.

The fixtures mirror the layouts documented in the corresponding modules and are
deliberately small; they exist so the parsers can be tested without shipping any
copyrighted data.
"""

from __future__ import annotations

import gzip
import struct
import zlib
from pathlib import Path
from typing import Iterable


def build_farc(entries: Iterable[tuple[str, bytes]], compressed: bool = False) -> bytes:
    """Build a Sega FArc container.

    ``compressed`` selects the ``FArC`` variant, whose records carry a fourth
    field (uncompressed size) and whose payloads are gzip streams.
    """
    records = list(entries)
    table = bytearray()
    for name, data in records:
        table += name.encode("ascii") + b"\x00"
        table += b"\x00" * (12 if compressed else 8)
    first_data = 12 + len(table)

    offsets: list[int] = []
    payloads: list[bytes] = []
    cursor = first_data
    for _name, data in records:
        payload = gzip.compress(data) if compressed else data
        offsets.append(cursor)
        payloads.append(payload)
        cursor += len(payload)

    body = bytearray()
    idx = 0
    for name, data in records:
        body += name.encode("ascii") + b"\x00"
        body += struct.pack(">II", offsets[idx], len(payloads[idx]))
        if compressed:
            body += struct.pack(">I", len(data))
        idx += 1

    header = b"FArC" if compressed else b"FArc"
    header += struct.pack(">II", first_data - 8, 1)
    return header + bytes(body) + b"".join(payloads)


def build_adx(sample_count: int = 44100, channels: int = 2, loop: bool = False) -> bytes:
    header = struct.pack(">HH", 0x8000, 0x20)
    header += bytes([3, 18, 4, channels])
    header += struct.pack(">II", 44100, sample_count)
    header += struct.pack(">H", 500)
    header += bytes([3, 0x01 if loop else 0x00])
    if loop:
        header += struct.pack(">IIII", 100, 0x20, 200, 0x40)
    else:
        header += b"\x00" * 16
    return header + b"\x00" * 32


def build_sfo(fields: dict[str, str | int]) -> bytes:
    keys = list(fields)
    key_blob = bytearray()
    key_offsets: dict[str, int] = {}
    for key in keys:
        key_offsets[key] = len(key_blob)
        key_blob += key.encode("ascii") + b"\x00"

    data_blob = bytearray()
    index = bytearray()
    for key in keys:
        value = fields[key]
        if isinstance(value, int):
            raw, fmt = struct.pack("<I", value), 0x0404
        else:
            raw, fmt = value.encode("utf-8") + b"\x00", 0x0204
        data_off = len(data_blob)
        data_blob += raw
        index += struct.pack("<HHIII", key_offsets[key], fmt, len(raw), len(raw), data_off)

    key_tab = 20 + len(index)
    data_tab = key_tab + len(key_blob)
    header = b"\x00PSF" + struct.pack("<IIII", 0x00000101, key_tab, data_tab, len(keys))
    return header + bytes(index) + bytes(key_blob) + bytes(data_blob)


def build_self(entry: int = 0x20000, phnum: int = 2) -> bytes:
    """Build a minimal SELF header with a plaintext embedded ELF header."""
    buf = bytearray(0x500)
    struct.pack_into(">II", buf, 0x00, 0x53434500, 2)
    struct.pack_into(">HH", buf, 0x08, 1, 1)
    struct.pack_into(">I", buf, 0x0C, 0x4A0)
    struct.pack_into(">Q", buf, 0x10, 0x4C0)
    struct.pack_into(">Q", buf, 0x18, 0x400)
    struct.pack_into(">Q", buf, 0x20, 3)
    struct.pack_into(">Q", buf, 0x28, 0x70)
    struct.pack_into(">Q", buf, 0x30, 0x90)
    struct.pack_into(">Q", buf, 0x38, 0xD0)
    struct.pack_into(">Q", buf, 0x40, 0x400)
    struct.pack_into(">Q", buf, 0x48, 0x290)
    struct.pack_into(">Q", buf, 0x50, 0x390)
    struct.pack_into(">Q", buf, 0x58, 0x3C0)
    struct.pack_into(">Q", buf, 0x60, 0x100)

    e = 0x90
    buf[e : e + 4] = b"\x7fELF"
    buf[e + 4] = 2
    buf[e + 5] = 2
    buf[e + 7] = 0x66
    struct.pack_into(">H", buf, e + 16, 2)
    struct.pack_into(">H", buf, e + 18, 21)
    struct.pack_into(">Q", buf, e + 24, entry)
    struct.pack_into(">Q", buf, e + 32, 0x40)
    struct.pack_into(">I", buf, e + 48, 0)
    struct.pack_into(">H", buf, e + 56, phnum)
    struct.pack_into(">H", buf, e + 60, 0)

    phdrs = [
        (1, 0x00040005, 0x000000, 0x10000, 0x10000, 0x1000, 0x1000, 0x10000),
        (1, 0x00060006, 0x4B0000, 0x4C0000, 0x4C0000, 0x2000, 0x22000, 0x10000),
    ]
    for i, ph in enumerate(phdrs[:phnum]):
        struct.pack_into(">IIQQQQQQ", buf, 0xD0 + i * 0x38, *ph)

    # Section-info table: 8 entries of 0x20 bytes between 0x290 and 0x390.
    for i in range(8):
        struct.pack_into(">QQII", buf, 0x290 + i * 0x20, 0x4C0 + i * 0x10, 0x10, 1, 0)
    return bytes(buf)


def build_psarc(entries: int = 4, block_size: int = 0x10, valid: bool = True) -> bytes:
    header = bytearray(0x100)
    header[0:4] = b"PSAR"
    struct.pack_into(">I", header, 4, 0x00010004)
    header[8:12] = b"zlib"
    struct.pack_into(">IIIII", header, 12, 0x100 + entries * 30, 30, entries, block_size, 0)

    toc = bytearray()
    for i in range(entries):
        toc += bytes(16)
        if valid:
            toc += struct.pack(">III", i, 0x100, i) + b"\x00\x00"
        else:
            toc += b"\xde\xad\xbe\xef" * 3 + b"\x00\x00"
    payload = zlib.compress(b"x" * 512)
    return bytes(header) + bytes(toc) + payload


def write(path: Path, data: bytes) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path
