# Build

Status: **the native build has never been executed on this host.** No C/C++
compiler, CMake or Ninja is installed. Everything below is the procedure to run
once that prerequisite exists; it is marked planned, not validated.

## Prerequisites

| Component | Version | Why |
|---|---|---|
| Visual Studio Build Tools 2022 | 17.x, "Desktop development with C++" | MSVC provides `cl`; the generated code uses `__declspec(thread)` |
| CMake | ≥ 3.20 | build generation |
| Ninja | ≥ 1.11 | fast incremental builds |
| Windows SDK | 10.0.22621 or newer | D3D12 headers |

`clang-cl` is an acceptable substitute for `cl` if MSVC's STL is available.

## Stage 1 — extract the package

```bash
python .vendor/ps3recomp/tools/pkg_extract.py "$SKYCLIMAX_PKG" work/pkg
```

Validated: 46 files, 551 MB, no errors.

## Stage 2 — obtain a decrypted executable

Blocked. See [known issues](../troubleshooting/known-issues.md). The expected
artefact is `work/game/EBOOT.elf`, a PPC64 big-endian `ET_EXEC` image.

## Stage 3 — load

```bash
python .vendor/ps3recomp/tools/ppu_loader.py work/game/EBOOT.elf -o work/meta
```

Produces `EBOOT.functions.json`, `.image.json`, `.loader.json`, `.imports.json`.
The import list is what tells you which HLE modules must exist; on a decrypted
image expect the counts to be in the hundreds of NIDs, as the reference projects
report for comparable titles.

## Stage 4 — lift

```bash
python .vendor/ps3recomp/tools/ppu_lifter.py work/game/EBOOT.elf \
  -o generated/ \
  --functions work/meta/EBOOT.functions.json \
  --imports  work/meta/EBOOT.imports.json
```

Validated on a synthetic ELF: 1 function produced `ppu_recomp_000.cpp`
(1,117 lines) plus `ppu_recomp.h`.

## Stage 5 — stubs

```bash
python .vendor/ps3recomp/tools/generate_stubs.py work/meta/EBOOT.imports.json -o src/hle
```

Not yet executed against real imports, because the import table is encrypted.

## Stage 6 — configure and build

```bash
cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=RelWithDebInfo
cmake --build build
```

Not executed. Expected first failure on a real image is a missing HLE symbol,
which is the normal way this stage announces which module is unimplemented next.

## Stage 7 — run

```bash
./build/skyclimax.exe --log-level info
```

Not executed.

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
