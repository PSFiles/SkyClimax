# Executable analysis

Source: a decrypted `EBOOT.elf` supplied locally by the project owner,
5,653,432 bytes, SHA-256
`d3a13dd3eeb388e61cfec72a507821b018fa9cafe01e520982cfc30d6d33b777`.

The file was accepted only after it matched the encrypted container's own
declaration: `e_machine = 21` (`EM_PPC64`), `e_type = 2` (`ET_EXEC`),
`e_entry = 0x4CDF00`, 8 program headers, 31 section headers, and a size equal to
the `elf_size` field in the SELF header (`0x5643B8`).

Reproduce with:

```bash
python -m skyclimax self-info work/pkg/USRDIR/EBOOT.BIN
python .vendor/ps3recomp/tools/ppu_loader.py work/game/EBOOT.elf -o work/meta
```

## Container

| Field | Value |
|---|---|
| magic | `SCE\0` |
| SELF version | 2 |
| key revision | 1 (retail, signed and encrypted) |
| metadata size | 1,184 |
| header span | 2,688 (`0xA80`) |
| contained ELF size | 5,653,432 (`0x5643B8`) |
| program headers | 8 |
| section headers | 31 |

## Embedded ELF header

| Field | Value | Meaning |
|---|---|---|
| class | 2 | ELF64 |
| data | 2 | big-endian |
| OSABI | `0x66` | PlayStation 3 |
| `e_type` | 2 | `ET_EXEC` — fixed load address, no relocations |
| `e_machine` | 21 | `EM_PPC64` |
| `e_entry` | `0x4CDF00` | OPD descriptor, not code |
| `e_flags` | 0 | |

## Program headers

| # | type | perms | vaddr | filesz | memsz | bss |
|---|---|---|---|---|---|---|
| 0 | `PT_LOAD` | R+X | `0x10000` | `0x4A7060` | `0x4A7060` | 0 |
| 1 | `PT_LOAD` | R+W | `0x4C0000` | `0xB1B14` | `0x12554A8` | `0x11A3994` |
| 2 | `PT_LOAD` | R | 0 | 0 | 0 | 0 |
| 3 | `PT_LOAD` | R+W | 0 | 0 | 0 | 0 |
| 4 | `PT_LOAD` | R+W | 0 | 0 | 0 | 0 |
| 5 | `PT_TLS` | R | `0x4EF27C` | 4 | `0x1EC` | `0x1E8` |
| 6 | `0x60000001` | – | `0x4B7000` | `0x20` | `0x20` | 0 |
| 7 | `0x60000002` | – | `0x4B7020` | `0x40` | `0x40` | 0 |

The entry point sits in program header 1, which is `R+W` and not executable —
the classic OPD layout. Resolving it yields:

```text
entry (OPD)      : 0x4cdf00 -> code 0x10230, toc 0x4ed088
module TOC (r2)  : 0x4ed088
OPD region       : 0x4cdef0 size 0x17198
```

The first instructions of `0x10230` confirm it: `li r2,0; oris r2,r2,0x4c;
ori r2,r2,0xdf00; lwz r2,4(r2)` loads the TOC word from `OPD+4`.

## Decryption status

Decrypted by the owner, outside this repository. The payload was verified before
use:

| Check | Observed |
|---|---|
| entropy of segment 0, first 64 KiB, while encrypted | 7.9973 bits/byte |
| decodable instructions in `.text` | 1,109,100 of 1,219,608 words (90.9 %) |
| function table | non-empty, 11,338 unique entries |

The remaining 9.1 % of the text segment is data and alignment padding
interleaved with code, which is normal for this toolchain.

## Function inventory

| Metric | Value | Source |
|---|---|---|
| OPD descriptors | 11,827 | `ppu_loader.py` |
| unique functions (OPD-derived) | 11,338 | `ppu_loader.py` |
| functions after Ghidra analysis | 11,541 | `ghidra_analyze.py` |
| symbols | 118,346 | `ghidra_analyze.py` |
| referenced strings | 3,140 | `ghidra_analyze.py` |
| functions emitted by the lifter | 15,237 | `ppu_lifter.py` |
| unique call targets | 5,678 | `ppu_lifter.py` |

The lifter emits more functions than the OPD table because it also creates
tail-entry wrappers (3,397 of them) for addresses reached only by tail calls.

## Firmware imports

207 imports across 14 libraries:

| Library | Functions |
|---|---|
| `sysPrxForUser` | 32 |
| `cellGcmSys` | 27 |
| `sceNp` | 25 |
| `cellSpurs` | 24 |
| `cellSysutil` | 23 |
| `sys_fs` | 19 |
| `cellResc` | 12 |
| `cellAudio` | 11 |
| `sceNpTrophy` | 9 |
| `cellNetCtl` | 8 |
| `sys_io` | 6 |
| `cellGame` | 6 |
| `cellSync` | 3 |
| `cellSysmodule` | 2 |

Resolving the NIDs against the toolkit's database names 163 of 207; the
remaining 44 are absent from that database, not unknown to the game.

**Library names come from the libstub table and are authoritative.** The NID
database records canonical module names, which differ: the six `cellPad`
functions are exported through `sys_io`, and sixteen `cellFs` functions through
`sys_fs`. Reading the NID database alone would wrongly conclude the title has no
controller support.

## Instruction profile

Measured over the text segment with capstone (PPC64, big-endian), resynchronising
after undecodable words:

| Group | Share |
|---|---|
| integer | 31.8 % |
| load/store | 27.5 % |
| branch | 12.2 % |
| float | 7.9 % |
| vector (VMX) | 1.3 % |
| other | 19.3 % |

Most frequent mnemonics: `lwz` 8.3 %, `stw` 6.1 %, `addi` 4.9 %, `ld` 4.6 %,
`li` 4.4 %, `mr` 3.9 %, `bl` 3.8 %, `clrldi` 3.8 %. There are 42,620 direct
`bl` calls.

The low VMX share (1.3 %) is notable: this title is not vector-heavy, so the
paired-single and VMX128 edge cases that dominate other PS3 ports are less
exposed here. That is an observation about static instruction counts, not a
guarantee about which instructions run.

## Engine identification

Recovered from referenced strings, not guessed:

| Evidence | Meaning |
|---|---|
| `AM2M_InitMotionWorkEx` | Sega AM2 motion library |
| `extract_aet_node` | Sega AET particle/effect format |
| `create_aircraft`, `set_object_node_matrix`, `load_objset_texture`, `create_object_index_buffer` | model/objset subsystem |
| `evt_init_pursuit_emy`, `evt_init_search_light`, `evt_init_fly_xb70_kill` | mission event scripts |
| `efc_smoke_job`, `efc_smoke_buff`, `efc_cloud_buff` | SPU effect job and buffers |
| `CRI Audio/PS3PPU Ver.3.44.03`, `CRI ADX Decoder/PS3SPU Ver.1.00.07` | CRI middleware, built 2009-10-30 |
| `ENEPACK_ERROR_*` | Sega packing library error codes |

`efc_smoke_job` matters for scope: the title runs at least one SPURS job for
smoke effects, so SPU execution is not limited to audio. Audio itself is CRI's
own decoder (present for both PPU and SPU), which supports decoding ADX on the
host instead of executing the SPU audio path (ADR-0007).

## Next step

The lifted sources are complete but nothing has been compiled. Building requires
two things that are not in the binary release: a C/C++ toolchain, and the
toolkit's runtime sources (`ppu_load_elf`, `ppu_recomp_register`, `ppu_hle_init`,
`ppu_run`), which the project template links from `PS3RECOMP_DIR`. See
[the build guide](../build/build.md).
