# Compatibility matrix

Three states are used consistently: **planned** (designed, no code), **implemented**
(code exists), **validated** (exercised with a recorded command and result).

## Analysis tooling

| Capability | State | Evidence |
|---|---|---|
| PKG header parsing | validated | `skyclimax pkg-info`, 46 items, size matches file |
| PKG extraction | validated | 46 files extracted, `(pycryptodome)` fast path |
| SELF header parsing | validated | entry `0x4CDF00`, 8 phdrs, `entry_in_data_segment: true` |
| Decrypted ELF verification | validated | `e_machine=21`, `e_entry=0x4CDF00`, size `0x5643B8` |
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
| ELF load + OPD resolution | validated | 11,827 descriptors → 11,338 functions, TOC `0x4ed088` |
| Firmware import extraction | validated | 207 imports across 14 libraries |
| NID resolution | validated | 163 of 207 named by the toolkit database |
| PPC64 disassembly | validated | 1,109,100 instructions decoded (90.9 % of text) |
| C++ generation | validated | 15,237 functions, 17 chunks, 9,571,078 lines |
| Lift completeness | validated | 2 warnings in 15,237 functions, both at segment end |
| HLE call wiring | validated | 224 `ps3_hle_call` sites in generated code |
| C++ compilation | planned | no compiler (KI-003) |
| Native link | planned | needs runtime sources (KI-009) |
| Runtime boot | planned | depends on the two above |

## Ghidra

| Capability | State | Evidence |
|---|---|---|
| Headless launch | validated | usage banner with JDK 25 |
| PPC64 BE ELF import | validated | `PowerPC:BE:64:64-32addr` |
| Full auto-analysis | validated | 358 s, analysis succeeded |
| Function/symbol/string export | validated | 11,541 functions, 118,346 symbols, 3,140 strings |

## REA

| Capability | State | Evidence |
|---|---|---|
| CLI runs | validated | `--version` → `6.9.0` |
| Capability report | validated | 624-line report, 4 providers |
| Ghidra provider on Windows | unavailable for PPU | PE-only admission (KI-005) |
| Evidence workflow | implemented | not exercised on PPU data |

## Game subsystems

| Subsystem | State | Note |
|---|---|---|
| PPU execution | planned | code lifted, not compiled |
| SPU execution | planned | `cellSpurs` 24 imports, `efc_smoke_job` present |
| RSX / GCM rendering | planned | 101 Cg programs must be translated |
| Audio (ADX/AFS) | planned | CRI decoders present for PPU and SPU; host decoding preferred (ADR-0007) |
| Input (cellPad) | planned | 6 imports, exported through `sys_io` |
| File system (cellFs) | planned | 19 `sys_fs` imports; archive layer blocked by KI-002 |
| Save data (cellSaveData) | planned | not imported by this title |
| Trophies (NP) | planned | `sceNpTrophy` 9 imports, `TROPHY.TRP` present |
| Networking | planned | `sceNp` 25, `cellNetCtl` 8 imports |

## Validation log

| Date | Command | Result |
|---|---|---|
| 2026-11-14 | `pytest` | 22 passed (16 unit, 6 integration) |
| 2026-11-14 | `skyclimax self-info EBOOT.BIN` | 8 phdrs, entry `0x4CDF00` |
| 2026-11-14 | `analyzeHeadless -import smoke.elf` | import succeeded |
| 2026-11-14 | `rea capabilities` | 4 providers, Ghidra PE-only on Windows |
| 2026-11-14 | `ppu_loader.py EBOOT.elf` | 11,338 functions, 207 imports |
| 2026-11-14 | `ghidra_analyze.py EBOOT.elf` | 11,541 functions, 358 s analysis |
| 2026-11-14 | `ppu_lifter.py EBOOT.elf` | 15,237 functions, 9m10s, 2 warnings |
