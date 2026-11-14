# Architecture

## Shape of the system

SkyClimax is a thin, game-specific layer on top of the ps3recomp backend. It
does not reimplement a recompiler; it configures one and adds the analysis and
compatibility code that After Burner Climax specifically needs.

```text
  retail .pkg
      │  pkg_extract.py (public PS3_GPKG key)
      ▼
  EBOOT.BIN (SELF, encrypted)
      │  [BLOCKED: app key / decrypted dump]
      ▼
  EBOOT.elf (PPC64 BE, ET_EXEC, entry 0x4CDF00)
      │  ppu_loader.py   → image + OPD function table + NID imports
      │  ppu_disasm.py   → PPC64 listing
      │  ppu_lifter.py   → ppu_recomp_*.cpp  (one C++ function per guest function)
      ▼
  generated C++
      │  MSVC / clang-cl + CMake + Ninja   [BLOCKED: no compiler on this host]
      ▼
  skyclimax.exe  ──links──▶  ps3recomp runtime (HLE modules, RSX, SPU)
      │
      ├── cellGcmSys / RSX  → D3D12 backend
      ├── cellAudio / ADX   → host audio
      ├── cellPad           → XInput
      └── cellFs / cellSysutil / sysPrxForUser
```

## Layers and ownership

| Layer | Owner | Contents |
|---|---|---|
| Container readers | SkyClimax | `src/skyclimax/*.py` — PKG header, SELF header, PARAM.SFO, FArc, ADX, PSARC, inventory |
| Recompiler | ps3recomp (vendored) | loader, disassembler, lifter, stub generator |
| Runtime | ps3recomp (vendored) | `lib/ps3recomp_runtime.lib`, HLE modules, RSX translation |
| Game-specific compatibility | SkyClimax | stub overrides and per-title configuration, added only when evidence demands it |
| Build | SkyClimax | CMake glue, scripts, CI |

The boundary is deliberate: SkyClimax never patches the vendored tools. If a
backend change is needed it is expressed as a patch file under `tools/patches/`
so the vendored version stays pinned and auditable.

## Data flow contract

Each stage consumes and produces files, never in-memory state:

| Stage | Input | Output |
|---|---|---|
| extract | `.pkg` | `work/pkg/**` |
| inspect | `EBOOT.BIN` | `work/reports/self.json` |
| load | `EBOOT.elf` | `*.functions.json`, `*.image.json`, `*.imports.json` |
| lift | ELF + function table | `ppu_recomp_*.cpp`, `ppu_recomp.h` |
| build | generated C++ + runtime | `skyclimax.exe` |

This makes every stage individually reproducible and individually testable,
which is the only way the project stays debuggable when a 14,000-function lift
produces a wrong pixel three stages later.

## Interfaces between guest and host

Three interfaces carry almost all of the risk:

1. **Guest memory.** The recompiled code dereferences guest addresses. The
   runtime provides big-endian `vm_read*`/`vm_write*` accessors over a reserved
   region; the host must never hand a raw guest pointer to host code.
2. **Indirect calls.** A guest function pointer is an OPD address, not a code
   address. Dispatch resolves OPD → code before calling the registered host
   function.
3. **Syscalls.** `sc` becomes a call into the HLE dispatcher. Anything not
   implemented must fail loudly with the syscall number and the caller's
   address, never silently return zero.

## Why this shape and not another

- **Not a from-scratch lifter.** Writing a PPC64 lifter that handles VMX128,
  paired-single floats and the 32-bit ABI correctly is a multi-month project on
  its own, and nine reference projects already depend on one implementation.
  Duplicating it would add risk without adding capability.
- **Not an emulator.** The goal is native execution; an interpreter in the loop
  contradicts the premise.
- **Not a per-game renderer.** The Cg/RSX translation is shared infrastructure;
  keeping it out of game code is what makes the next title cheaper.

## Current position in the pipeline

| Milestone | State |
|---|---|
| M0 toolchain installed and validated | validated |
| M1 package opened, inventory reproducible | validated |
| M2 executable container analysed | validated |
| M3 lift pipeline proven on a synthetic ELF | validated |
| M4 native build of lifted code | planned — blocked, no compiler, no runtime sources |
| M5 decrypted EBOOT lifted | validated — 15,237 functions |
| M6 runtime boot and first frame | planned |
| M7 playable | planned |

The project is **experimental**. The last milestone actually reached is M5: the
image is lifted, but nothing has been compiled or run.
