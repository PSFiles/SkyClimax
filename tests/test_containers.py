"""Container parser tests against synthetic fixtures."""

from __future__ import annotations

import json

import pytest
from conftest import build_adx, build_farc, build_psarc, build_self, build_sfo, write

from skyclimax.adx import parse_adx
from skyclimax.cli import main
from skyclimax.farc import extract_all, parse_farc
from skyclimax.inventory import build_inventory, classify
from skyclimax.pkg import parse_pkg_header
from skyclimax.psarc import parse_psarc
from skyclimax.selfheader import parse_self_header
from skyclimax.sfo import parse_sfo


def test_farc_plain_roundtrip(tmp_path):
    archive_path = write(tmp_path / "plain.farc", build_farc([("a.png", b"AAAA"), ("b.txt", b"BB")]))
    archive = parse_farc(archive_path)
    assert archive.variant == "plain"
    assert [e.name for e in archive.entries] == ["a.png", "b.txt"]
    assert [e.size for e in archive.entries] == [4, 2]
    out = extract_all(archive, tmp_path / "out")
    assert [p.read_bytes() for p in out] == [b"AAAA", b"BB"]


def test_farc_compressed_variant_uses_gzip(tmp_path):
    archive_path = write(
        tmp_path / "cmp.farc", build_farc([("s.vp", b"vertex" * 100)], compressed=True)
    )
    archive = parse_farc(archive_path)
    assert archive.variant == "compressed"
    entry = archive.entries[0]
    assert entry.compressed is True
    assert entry.size < entry.uncompressed_size
    written = extract_all(archive, tmp_path / "out")[0]
    assert written.read_bytes() == b"vertex" * 100


def test_farc_rejects_truncated_entry(tmp_path):
    data = bytearray(build_farc([("a.bin", b"0123456789")]))
    data[-20:-16] = b"\x7f\xff\xff\xff"  # claim a size far beyond EOF
    path = write(tmp_path / "bad.farc", bytes(data))
    with pytest.raises(ValueError):
        parse_farc(path)


def test_farc_rejects_bad_magic(tmp_path):
    path = write(tmp_path / "bad.farc", b"NOPE" + b"\x00" * 32)
    with pytest.raises(ValueError):
        parse_farc(path)


def test_adx_header_and_loop(tmp_path):
    plain = parse_adx(write(tmp_path / "a.adx", build_adx(sample_count=88200)))
    assert (plain.channels, plain.sample_rate, plain.sample_count) == (2, 44100, 88200)
    assert plain.duration_seconds == pytest.approx(2.0)
    assert plain.loop is None

    looped = parse_adx(write(tmp_path / "b.adx", build_adx(loop=True)))
    assert looped.loop == {"start_sample": 100, "start_byte": 0x20, "end_sample": 200, "end_byte": 0x40}


def test_adx_rejects_bad_signature(tmp_path):
    with pytest.raises(ValueError):
        parse_adx(write(tmp_path / "x.adx", b"\x00" * 32))


def test_sfo_strings_and_integers(tmp_path):
    fields = {"TITLE": "After Burner Climax", "TITLE_ID": "NPUB30151", "PARENTAL_LEVEL": 4}
    entries = parse_sfo(write(tmp_path / "PARAM.SFO", build_sfo(fields)))
    assert entries["TITLE"].value == "After Burner Climax"
    assert entries["TITLE_ID"].value == "NPUB30151"
    assert entries["PARENTAL_LEVEL"].value == 4


def test_sfo_rejects_bad_magic(tmp_path):
    with pytest.raises(ValueError):
        parse_sfo(write(tmp_path / "x.sfo", b"PSF\x00" + b"\x00" * 32))


def test_self_header_layout(tmp_path):
    header = parse_self_header(write(tmp_path / "EBOOT.BIN", build_self(entry=0x4CDF00)))
    assert header.is_retail is True
    assert header.elf_machine == 21  # EM_PPC64
    assert header.elf_type == 2  # ET_EXEC
    assert header.elf_entry == 0x4CDF00
    assert len(header.program_headers) == 2
    text, data = header.program_headers
    assert text.permissions == "XR"
    assert data.permissions == "WR"
    assert data.bss_size == 0x20000
    # The PS3 entry point is an OPD descriptor, i.e. inside the data segment.
    assert header.entry_in_data_segment is True
    assert len(header.section_info) == 8


def test_self_rejects_bad_magic(tmp_path):
    with pytest.raises(ValueError):
        parse_self_header(write(tmp_path / "x.bin", b"\x00" * 0x200))


def test_psarc_toc_parsed_when_layout_matches(tmp_path):
    header = parse_psarc(write(tmp_path / "ok.psarc", build_psarc(entries=4)))
    assert header.toc_state == "parsed"
    assert header.toc_entry_count == 4
    assert header.compression == "zlib"


def test_psarc_toc_reported_opaque_when_layout_does_not_match(tmp_path):
    header = parse_psarc(write(tmp_path / "bad.psarc", build_psarc(entries=4, valid=False)))
    assert header.toc_state == "opaque"
    assert header.entries == []
    assert "treated as unreadable" in header.toc_reason


def test_pkg_header_fields(tmp_path):
    buf = bytearray(0x400)
    buf[0:4] = b"\x7fPKG"
    buf[0x30:0x30 + 33] = b"UP0177-NPUB30151_00-AFTERBURNERCM"
    import struct

    struct.pack_into(">I", buf, 4, 0x80000001)
    struct.pack_into(">I", buf, 0x14, 46)
    struct.pack_into(">Q", buf, 0x18, len(buf))
    header = parse_pkg_header(write(tmp_path / "x.pkg", bytes(buf)))
    assert header.item_count == 46
    assert header.size_matches_file is True
    assert header.content_id.startswith("UP0177-NPUB30151")


def test_classify_uses_magic_not_extension():
    assert classify(b"PSAR\x00\x01")[0] == "psarc"
    assert classify(b"FArC\x00\x00")[0] == "farc"
    assert classify(b"SCE\x00\x00\x00")[0] == "self"
    assert classify(b"????")[0] == "unknown"


def test_inventory_counts_and_hashes(tmp_path):
    write(tmp_path / "a.bin", b"SCE\x00" + b"\x00" * 12)
    write(tmp_path / "sub" / "b.dat", b"PSAR" + b"\x00" * 12)
    inv = build_inventory(tmp_path)
    assert inv.to_dict()["file_count"] == 2
    kinds = {f.kind for f in inv.files}
    assert kinds == {"self", "psarc"}
    assert all(len(f.sha256) == 64 for f in inv.files)


def test_cli_writes_json_and_reports_errors(tmp_path, capsys):
    sfo_path = write(tmp_path / "PARAM.SFO", build_sfo({"TITLE": "X"}))
    target = tmp_path / "out" / "sfo.json"
    assert main(["sfo", str(sfo_path), "--json", str(target)]) == 0
    assert json.loads(target.read_text())["fields"]["TITLE"] == "X"

    assert main(["sfo", str(tmp_path / "missing.sfo")]) == 1
    assert "error:" in capsys.readouterr().err
