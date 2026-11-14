# Compatibility matrix

Three states are used consistently: **planned** (designed, no code), **implemented**
(code exists), **validated** (exercised with a recorded command and result).

## Analysis tooling

| Capability | State | Evidence |
|---|---|---|
| PKG header parsing | validated | `skyclimax pkg-info`, 46 items, size matches file |
| PKG extraction | validated | 46 files extracted, `(pycryptodome)` fast path |
| SELF header parsing | validated | entry `0x4CDF00`, 8 phdrs, `entry_in_data_segment: true` |
| PARAM.SFO parsing | validated | `TITLE = After Burner Climax` |
| FArc plain variant | validated | `SYSTEM.farc`, 2 records, PNG payloads |
| FArc compressed variant | validated | `shader_cg.farc`, 101 records, gzip payloads |
| ADX header parsing | validated | 23 files, 44.1 kHz, 1,898.9 s total |
| PSARC header parsing | validated | `PSAR`, `zlib`, 218 TOC entries |
| PSARC TOC parsing | blocked | `toc_state: opaque` (KI-002) |
| Inventory + hashing | validated | `skyclimax inventory`, SHA-256 per file |

## Recompilation pipeline

| Capability | State | Evidence |
|---|---|---|
| ELF load + OPD resolution | validated (synthetic) | `entry (OPD) 0x20000 -> code 0x10000, toc 0x20d00` |
| PPC64 disassembly | validated (synthetic) | lifter consumed the disassembly |
| C++ generation | validated (synthetic) | 1 function → 1,117 lines |
| C++ compilation | planned | no compiler (KI-003) |
| HLE stub generation | planned | needs a decrypted import table |
| Native link | planned | depends on the above |

## Ghidra

| Capability | State | Evidence |
|---|---|---|
| Headless launch | validated | usage banner with JDK 25 |
| PPC64 BE ELF import | validated | `PowerPC:BE:64:default`, import succeeded |
| Analysis of the real EBOOT | blocked | payload encrypted (KI-001) |

## REA

| Capability | State | Evidence |
|---|---|---|
| CLI runs | validated | `--version` → `6.9.0` |
| Capability report | validated | 624-line report, 4 providers |
| Ghidra provider on Windows | unavailable for PPU | PE-only admission (KI-005) |
| Evidence workflow | implemented | not exercised on PPU data |

## Game subsystems

Nothing below is implemented. They are listed so that the gap is explicit.

| Subsystem | State | Note |
|---|---|---|
| PPU execution | planned | depends on decryption |
| SPU execution | planned | unknown until imports are readable |
| RSX / GCM rendering | planned | 101 Cg programs must be translated |
| Audio (ADX/AFS) | planned | treated as data (ADR-0007, proposed) |
| Input (cellPad) | planned | |
| File system (cellFs) | planned | archive layer blocked by KI-002 |
| Save data (cellSaveData) | planned | |
| Trophies (NP) | planned | `TROPHY.TRP` present |
| Networking | planned | `NPWR00981` present; scope unknown |

## Validation log

| Date | Command | Result |
|---|---|---|
| 2026-11-14 | `pytest` | 16 passed |
| 2026-11-14 | `skyclimax self-info EBOOT.BIN` | 8 phdrs, entry `0x4CDF00` |
| 2026-11-14 | `analyzeHeadless -import smoke.elf` | import succeeded |
| 2026-11-14 | `rea capabilities` | 4 providers, Ghidra PE-only on Windows |
| 2026-11-14 | `ppu_lifter.py smoke.elf` | 1 function, 1,117 lines |
