"""Integration tests against the retail package.

These tests are skipped unless the local package has been extracted, so the
suite stays green on a clean checkout and in CI. They assert only values that
were verified by hand during the analysis phase.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from skyclimax.adx import parse_adx
from skyclimax.farc import parse_farc
from skyclimax.pkg import parse_pkg_header
from skyclimax.psarc import parse_psarc
from skyclimax.selfheader import parse_self_header
from skyclimax.sfo import parse_sfo

PACKAGE = Path(os.environ.get("SKYCLIMAX_PKG", "UP0177-NPUB30151_00-AFTERBURNERCMX00.pkg"))
EXTRACTED = Path(os.environ.get("SKYCLIMAX_EXTRACTED", "work/pkg"))

pytestmark = pytest.mark.skipif(
    not PACKAGE.is_file(), reason="retail package not present (set SKYCLIMAX_PKG)"
)


def test_pkg_header_matches_file():
    header = parse_pkg_header(PACKAGE)
    assert header.content_id == "UP0177-NPUB30151_00-AFTERBURNERCMX00"
    assert header.item_count == 46
    assert header.size_matches_file is True


@pytest.mark.skipif(not (EXTRACTED / "PARAM.SFO").is_file(), reason="package not extracted")
def test_param_sfo_identifies_title():
    fields = parse_sfo(EXTRACTED / "PARAM.SFO")
    assert fields["TITLE"].value == "After Burner Climax"
    assert fields["TITLE_ID"].value == "NPUB30151"
    assert fields["CATEGORY"].value == "HG"


@pytest.mark.skipif(not (EXTRACTED / "USRDIR/EBOOT.BIN").is_file(), reason="package not extracted")
def test_eboot_is_encrypted_retail_self():
    header = parse_self_header(EXTRACTED / "USRDIR/EBOOT.BIN")
    assert header.is_retail is True
    assert header.elf_machine == 21  # EM_PPC64
    assert header.elf_type == 2  # ET_EXEC
    assert header.elf_entry == 0x4CDF00
    assert header.elf_phnum == 8
    assert header.entry_in_data_segment is True


@pytest.mark.skipif(
    not (EXTRACTED / "USRDIR/ps3/shader_cg.farc").is_file(), reason="package not extracted"
)
def test_shader_archive_lists_vertex_and_fragment_programs():
    archive = parse_farc(EXTRACTED / "USRDIR/ps3/shader_cg.farc")
    assert archive.variant == "compressed"
    assert archive.entries, "shader archive must contain entries"
    suffixes = {Path(e.name).suffix for e in archive.entries}
    assert suffixes <= {".vp", ".fp"}


@pytest.mark.skipif(
    not (EXTRACTED / "USRDIR/rom/adx/ABC_BGM01.adx").is_file(), reason="package not extracted"
)
def test_music_stream_header():
    header = parse_adx(EXTRACTED / "USRDIR/rom/adx/ABC_BGM01.adx")
    assert header.sample_rate == 44100
    assert header.channels == 2
    assert header.encoding == 3


@pytest.mark.skipif(
    not (EXTRACTED / "USRDIR/ps3/rom.psarc").is_file(), reason="package not extracted"
)
def test_main_archive_toc_is_not_parseable():
    """Documents a real limitation: the TOC is opaque, so nothing is invented."""
    header = parse_psarc(EXTRACTED / "USRDIR/ps3/rom.psarc")
    assert header.toc_state == "opaque"
    assert header.entries == []
