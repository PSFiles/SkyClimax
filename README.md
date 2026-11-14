# SkyClimax

**Português do Brasil:** [README.pt-BR.md](README.pt-BR.md)

Static recompilation of **After Burner Climax** (PlayStation 3, `NPUB30151`) to
native Windows x64 — no emulator in the loop.

> **Status: experimental, but it runs.** The recompiled `SkyClimax.exe`
> (295.6 MB) boots, initialises D3D12, opens its own 407 MB archive and presents
> frames. It is **not playable**: the title then blocks in its event loop, and
> this host only has the WARP software rasterizer. See
> [status](docs/en-US/status.md) and
> [known issues](docs/en-US/troubleshooting/known-issues.md).

## What this repository is

A reproducible engineering project around the [ps3recomp](https://github.com/sp00nznet/ps3recomp)
static recompiler, plus the analysis tooling this specific title needs:

| Component | State |
|---|---|
| `src/skyclimax/` — PKG, SELF, PARAM.SFO, FArc, ADX, PSARC readers | implemented, tested |
| `scripts/check_docs_parity.py` — bilingual documentation gate | implemented, passing |
| `scripts/install-tools.*` — pinned, idempotent toolchain install | implemented |
| `.github/workflows/ci.yml` — Windows CI | implemented |
| Lifted game code (`generated/`) | **produced** — 15,237 functions, 9.57 M lines |
| Compiled executable | **produced** — `build/SkyClimax.exe`, 295.6 MB |
| Playable build | **not produced** — stalls in `event_queue_receive` |

## What is actually known about the game

Everything below was measured on the retail package, not assumed:

- Package `UP0177-NPUB30151_00-AFTERBURNERCMX00.pkg`, 551,772,592 bytes, 46 items.
- `PARAM.SFO`: title `After Burner Climax`, `TITLE_ID NPUB30151`, version `01.00`,
  target firmware `03.0000`.
- `EBOOT.BIN`: 5,656,176-byte retail SELF; embedded ELF is `ET_EXEC`, `EM_PPC64`,
  big-endian, entry `0x4CDF00` (an OPD descriptor in the data segment).
- Decrypted image (supplied by the owner, not in this repo): 11,338 functions
  from 11,827 OPD descriptors, 207 firmware imports across 14 libraries,
  1.11 M instructions decoded, engine symbols for AM2 motion, AET effects and
  CRI 3.44.03 audio recovered from strings.
- Assets: 407 MB PSARC (`rom.psarc`) whose table of contents is opaque, 101 Cg
  shader programs (`.vp`/`.fp`, gzip) in `shader_cg.farc`, 23 CRI ADX streams
  (31.6 minutes total) plus a 38.9 MB CRI AFS voice bank.

Details and evidence: [executable](docs/en-US/analysis/executable.md),
[assets](docs/en-US/analysis/assets.md), [package](docs/en-US/analysis/package.md).

## Requirements

| Requirement | Version | Notes |
|---|---|---|
| Windows | 10 or 11, x64 | developed and tested on Windows 11 23H2 |
| Python | 3.10+ | 3.13.14 used here |
| Ghidra | 12.2 | requires **JDK 25** |
| Node.js | 24.22.3 | only for REA; the bundled 22.22.2 is too old |
| ps3recomp | 0.19.0 | recompiler backend |
| MSVC + CMake + Ninja | 2022 / 3.20 / 1.11 | **not installed here** — required for M4 |

## Install

```bash
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e ".[dev]"
powershell -ExecutionPolicy Bypass -File scripts/install-tools.ps1
```

## Use

```bash
# describe the package header
python -m skyclimax pkg-info UP0177-NPUB30151_00-AFTERBURNERCMX00.pkg

# extract (needs the vendored ps3recomp tools)
python .vendor/ps3recomp/tools/pkg_extract.py UP0177-NPUB30151_00-AFTERBURNERCMX00.pkg work/pkg

# analyse the executable container
python -m skyclimax self-info work/pkg/USRDIR/EBOOT.BIN --json work/reports/self.json

# inventory every extracted file by magic
python -m skyclimax inventory work/pkg --json work/reports/inventory.json

# list or extract a Sega FArc archive
python -m skyclimax farc work/pkg/USRDIR/ps3/shader_cg.farc --extract work/shader

# verify the repository
.venv/Scripts/python.exe -m pytest
.venv/Scripts/python.exe scripts/check_docs_parity.py
```

## Milestones

| # | Milestone | State |
|---|---|---|
| M0 | toolchain installed and validated | validated |
| M1 | package opened, inventory reproducible | validated |
| M2 | executable container analysed | validated (metadata only) |
| M3 | lift pipeline proven on a synthetic ELF | validated |
| M4 | native build of lifted code | validated — 24 + 5 TUs, 0 errors |
| M5 | decrypted EBOOT lifted | validated — 15,237 functions |
| M6 | runtime boot, first frame | validated — frames presented |
| M7 | playable | planned |

## Known limitations

1. **It does not reach gameplay.** After presenting frames the title blocks in
   `event_queue_receive` (`cia=0x004E3480`), waiting for an event the runtime
   never delivers.
2. **`rom.psarc` is unindexed.** Its TOC does not match the documented layout;
   96 % of the package payload is currently unreadable.
3. **Nothing has been compiled.** No C/C++ toolchain exists on the development
   host, so the generated C++ is structurally verified only.
4. **REA cannot analyse PPU ELF on Windows.** Its Windows Ghidra provider accepts
   PE binaries only; Ghidra is therefore driven directly.

## Repository rules

- No game files, keys or decrypted payloads are committed. `.gitignore` enforces it.
- Documentation exists in en-US and pt-BR and is machine-checked for parity.
- A feature is `validated` only when a command and its output are recorded.

## Documentation

Start at [docs/README.md](docs/README.md) (bilingual index with parity status).
Architecture decisions: [docs/en-US/architecture/decisions.md](docs/en-US/architecture/decisions.md).

## Licence

MIT for the code in this repository. ps3recomp and Ghidra keep their own
licences. No proprietary Sega or Sony material is distributed here.
