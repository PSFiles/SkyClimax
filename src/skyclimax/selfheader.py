"""PlayStation 3 SELF (signed ELF) header reader.

Only the *outer* SELF container is parsed. The contained ELF is stored as
AES-encrypted segments in a retail package, so no section contents are exposed
here -- the goal is to recover layout metadata (entry point, segment map,
sizes) without decrypting anything.

Field offsets were verified against
``UP0177-NPUB30151_00-AFTERBURNERCMX00.pkg`` -> ``USRDIR/EBOOT.BIN``:

===== ==========================================================
0x000 ``SCE\\0`` magic, ``u32`` version
0x008 ``u16`` key revision, ``u16`` header type
0x00C ``u32`` metadata size
0x010 ``u64`` header span (matches the offset of the first payload)
0x018 ``u64`` contained ELF size
0x020 ``u64`` unknown (observed 3)
0x028 ``u64`` app-info offset
0x030 ``u64`` embedded ELF header offset
0x038 ``u64`` program-header table offset
0x040 ``u64`` section-header table offset
0x048 ``u64`` section-info table offset
0x050 ``u64`` SCE version header offset
0x058 ``u64`` control-info offset
0x060 ``u64`` control-info size
===== ==========================================================
"""

from __future__ import annotations

import struct
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

SELF_MAGIC = 0x53434500

PT_LOAD = 1
PT_SCE_PPURELA = 0x60000002

#: ``p_flags`` bits used by PS3 toolchains on top of the generic RWX bits.
PS3_FLAG_NAMES = {
    0x00000001: "X",
    0x00000002: "W",
    0x00000004: "R",
}


@dataclass
class ProgramHeader:
    index: int
    p_type: int
    p_flags: int
    p_offset: int
    p_vaddr: int
    p_paddr: int
    p_filesz: int
    p_memsz: int
    p_align: int

    @property
    def bss_size(self) -> int:
        return max(0, self.p_memsz - self.p_filesz)

    @property
    def permissions(self) -> str:
        return "".join(name for bit, name in sorted(PS3_FLAG_NAMES.items()) if self.p_flags & bit) or "-"

    def to_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "type": self.p_type,
            "flags": self.p_flags,
            "permissions": self.permissions,
            "offset": self.p_offset,
            "vaddr": self.p_vaddr,
            "paddr": self.p_paddr,
            "filesz": self.p_filesz,
            "memsz": self.p_memsz,
            "bss_size": self.bss_size,
            "align": self.p_align,
        }


@dataclass
class SelfHeader:
    path: Path
    file_size: int
    version: int
    key_revision: int
    header_type: int
    metadata_size: int
    header_span: int
    elf_size: int
    unknown_0x20: int
    appinfo_offset: int
    elf_offset: int
    phdr_offset: int
    shdr_offset: int
    section_info_offset: int
    sceversion_offset: int
    controlinfo_offset: int
    controlinfo_size: int
    #: Copied from the embedded ELF header (plaintext even when segments are not).
    elf_class: int = 0
    elf_endian: int = 0
    elf_osabi: int = 0
    elf_type: int = 0
    elf_machine: int = 0
    elf_entry: int = 0
    elf_phoff: int = 0
    elf_shoff: int = 0
    elf_flags: int = 0
    elf_phnum: int = 0
    elf_shnum: int = 0
    control_flags: int = 0
    program_headers: list[ProgramHeader] = field(default_factory=list)
    section_info: list[dict[str, int]] = field(default_factory=list)

    @property
    def is_retail(self) -> bool:
        """Key revision 1 identifies a retail (signed + encrypted) SELF."""
        return self.key_revision == 1

    @property
    def entry_in_data_segment(self) -> bool:
        """PS3 entry points are OPD descriptors, which live in the data segment."""
        for ph in self.program_headers:
            if ph.p_vaddr <= self.elf_entry < ph.p_vaddr + ph.p_memsz:
                return ph.permissions.find("X") < 0
        return False

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": str(self.path),
            "file_size": self.file_size,
            "version": self.version,
            "key_revision": self.key_revision,
            "retail_encrypted": self.is_retail,
            "header_type": self.header_type,
            "metadata_size": self.metadata_size,
            "header_span": self.header_span,
            "elf_size": self.elf_size,
            "offsets": {
                "appinfo": self.appinfo_offset,
                "elf_header": self.elf_offset,
                "program_headers": self.phdr_offset,
                "section_headers": self.shdr_offset,
                "section_info": self.section_info_offset,
                "sce_version": self.sceversion_offset,
                "control_info": self.controlinfo_offset,
            },
            "control_info_size": self.controlinfo_size,
            "control_flags": self.control_flags,
            "elf": {
                "class": self.elf_class,
                "endianness": self.elf_endian,
                "osabi": self.elf_osabi,
                "type": self.elf_type,
                "machine": self.elf_machine,
                "entry": self.elf_entry,
                "phoff": self.elf_phoff,
                "shoff": self.elf_shoff,
                "flags": self.elf_flags,
                "phnum": self.elf_phnum,
                "shnum": self.elf_shnum,
            },
            "program_headers": [ph.to_dict() for ph in self.program_headers],
            "section_info": self.section_info,
        }


def _u64(buf: bytes, offset: int) -> int:
    return struct.unpack(">Q", buf[offset : offset + 8])[0]


def parse_self_header(path: str | Path) -> SelfHeader:
    path = Path(path)
    raw = path.read_bytes()
    if len(raw) < 0x80:
        raise ValueError(f"{path}: too small to be a SELF ({len(raw)} bytes)")
    magic, version = struct.unpack(">II", raw[0:8])
    if magic != SELF_MAGIC:
        raise ValueError(f"{path}: not a SELF container (magic 0x{magic:08x})")

    key_revision, header_type = struct.unpack(">HH", raw[8:12])
    metadata_size = struct.unpack(">I", raw[12:16])[0]

    hdr = SelfHeader(
        path=path,
        file_size=len(raw),
        version=version,
        key_revision=key_revision,
        header_type=header_type,
        metadata_size=metadata_size,
        header_span=_u64(raw, 0x10),
        elf_size=_u64(raw, 0x18),
        unknown_0x20=_u64(raw, 0x20),
        appinfo_offset=_u64(raw, 0x28),
        elf_offset=_u64(raw, 0x30),
        phdr_offset=_u64(raw, 0x38),
        shdr_offset=_u64(raw, 0x40),
        section_info_offset=_u64(raw, 0x48),
        sceversion_offset=_u64(raw, 0x50),
        controlinfo_offset=_u64(raw, 0x58),
        controlinfo_size=_u64(raw, 0x60),
    )

    e = hdr.elf_offset
    if raw[e : e + 4] == b"\x7fELF":
        hdr.elf_class = raw[e + 4]
        hdr.elf_endian = raw[e + 5]
        hdr.elf_osabi = raw[e + 7]
        hdr.elf_type = struct.unpack(">H", raw[e + 16 : e + 18])[0]
        hdr.elf_machine = struct.unpack(">H", raw[e + 18 : e + 20])[0]
        hdr.elf_entry = _u64(raw, e + 24)
        hdr.elf_phoff = _u64(raw, e + 32)
        hdr.elf_shoff = _u64(raw, e + 40)
        hdr.elf_flags = struct.unpack(">I", raw[e + 48 : e + 52])[0]
        hdr.elf_phnum = struct.unpack(">H", raw[e + 56 : e + 58])[0]
        hdr.elf_shnum = struct.unpack(">H", raw[e + 60 : e + 62])[0]

    # Program headers: 0x38 bytes each on PPU64.
    for i in range(hdr.elf_phnum):
        base = hdr.phdr_offset + i * 0x38
        if base + 0x38 > len(raw):
            break
        p_type, p_flags, p_offset, p_vaddr, p_paddr, p_filesz, p_memsz, p_align = struct.unpack(
            ">IIQQQQQQ", raw[base : base + 0x38]
        )
        hdr.program_headers.append(
            ProgramHeader(i, p_type, p_flags, p_offset, p_vaddr, p_paddr, p_filesz, p_memsz, p_align)
        )

    # Section-info entries are 0x20 bytes on disk; the first 0x18 carry data and
    # the remainder is padding. The table is walked until the next known
    # structure (the SCE version header).
    count = (hdr.sceversion_offset - hdr.section_info_offset) // 0x20
    for i in range(max(0, count)):
        base = hdr.section_info_offset + i * 0x20
        if base + 0x20 > len(raw):
            break
        off, size, compressed, _pad = struct.unpack(">QQII", raw[base : base + 0x18])
        hdr.section_info.append(
            {"index": i, "offset": off, "size": size, "compressed": compressed}
        )

    if hdr.controlinfo_offset + 4 <= len(raw):
        hdr.control_flags = struct.unpack(">I", raw[hdr.controlinfo_offset + 0x0C : hdr.controlinfo_offset + 0x10])[0]

    return hdr
