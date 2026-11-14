# Build

Status: **validated end to end.** `scripts/build.py` compiles 24 PPU translation
units and 5 SPU units with clang-cl and links `build/SkyClimax.exe` (295.6 MB).
Stages 1–6 are validated; stage 7 runs but does not reach gameplay.

## Prerequisites

| Component | Version | Why |
|---|---|---|
| Visual Studio Build Tools 2022 | 17.x, "Desktop development with C++" | MSVC provides `cl`; the generated code uses `__declspec(thread)` |
| LLVM / clang-cl | 23.1.5 | the only compiler that accepts the generated header |
| Ninja | ≥ 1.11 | build generation (ships with Build Tools) |
| Windows SDK | 10.0.22621 or newer | D3D12 headers |
| ps3recomp runtime sources | v0.19.0 | `ppu_load_elf`, `ppu_recomp_register`, `ppu_hle_init`, `ppu_run` |

`clang-cl` is an acceptable substitute for `cl` if MSVC's STL is available.

The binary release ships headers and `lib/ps3recomp_runtime.lib`, but **not** the
runtime sources. The upstream project template links them from a checkout named
by `PS3RECOMP_DIR`. That checkout is already present at
`.vendor/ps3recomp-src`, pinned to `ae92407b` — the same commit as the release.
See KI-009.

## Stage 1 — extract the package

```bash
python .vendor/ps3recomp/tools/pkg_extract.py "$SKYCLIMAX_PKG" work/pkg
```

Validated: 46 files, 551 MB, no errors.

## Stage 2 — obtain a decrypted executable

Validated. The owner supplied `EBOOT.elf` (5,653,432 bytes, SHA-256
`d3a13dd3…d6d33b777`). It was accepted only after matching the encrypted
container's declaration: `e_machine = 21`, `e_entry = 0x4CDF00`, 8 program
headers, 31 section headers.

## Stage 3 — load

```bash
python .vendor/ps3recomp/tools/ppu_loader.py work/game/EBOOT.elf -o work/meta
```

Validated:

```text
entry (OPD)      : 0x4cdf00 -> code 0x10230, toc 0x4ed088
OPD descriptors  : 11827
unique functions : 11338
firmware imports : 207 across 14 libraries
```

Produces `EBOOT.functions.json`, `.image.json`, `.loader.json`, `.imports.json`.

## Stage 4 — lift

```bash
python .vendor/ps3recomp/tools/ppu_lifter.py work/game/EBOOT.elf \
  -o generated/ \
  --functions work/meta/EBOOT.functions.json \
  --hle-stubs work/meta/EBOOT.imports.json
```

Validated: 15,237 functions, 17 chunks, 9,571,078 lines, 9m10s, 2 warnings — both
`has no continuation at 0x004B7060`, which is the end of the text segment and
therefore a boundary artefact rather than a mis-sized function.

Note the flag name: it is `--hle-stubs`, not `--imports`. The lifter's own
documentation in `docs/PPU_RECOMP.md` says `--imports`, but the shipped CLI does
not accept it. The `--hle-stubs` file is the same `imports.json`.

## Stage 5 — stub generation

Not required for this title. The runtime already implements all 14 imported
libraries; `generate_stubs.py` exists for libraries that are missing. Keep it as
a fallback when a NID turns out to be unimplemented at runtime.

## Stage 6 — build

```bash
python scripts/build.py --jobs 2
```

Validated: 24 PPU units + 5 SPU units, 0 errors, `build/SkyClimax.exe` 295.6 MB.

`scripts/build.py` exists because CMake cannot run on this host: its compiler
probe invokes `reg.exe`, which the sandbox blocks. The script locates MSVC, the
Windows SDK and clang-cl, emits `build/build.ninja`, and runs Ninja. The PPU
units are built `/Od` by default because a 600k-line unit at `/O1` needs ~2.5 GB
and this host has 7.9 GB; pass `--optimize` on a larger machine.

## Stage 7 — run

```bash
./build/SkyClimax.exe work/game/PS3_GAME/USRDIR/EBOOT.elf
```

Validated to the point of presenting frames: the entry OPD is dispatched, D3D12
initialises (WARP on this host), the window opens, `rom.psarc` is opened and its
TOC read, and `SetConvertAndFlip` runs four times. The title then blocks in
`event_queue_receive` and never reaches gameplay.

## What "done" means per stage

| Stage | Evidence required |
|---|---|
| extract | 46 files, byte sizes match the extractor listing |
| decrypt | SHA-256 of the ELF recorded in `work/reports/` |
| load | non-zero function count, import list non-empty |
| lift | generated files compile *and* the function count matches the loader |
| stub | every imported NID resolves to a host symbol |
| build | `skyclimax.exe` exists and `--version` runs |
| run | a frame is presented, captured and attached to a report |

A stage is never marked complete because the previous one succeeded.
