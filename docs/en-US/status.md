# Status and task log

Last updated: 2026-11-14.

## Current position

**Milestone reached: M5 — the decrypted executable is loaded and lifted.** The
project is experimental. 15,237 functions have been translated to C++, but
nothing has been compiled and nothing has run.

| Milestone | State | Blocking issue |
|---|---|---|
| M0 toolchain installed and validated | validated | — |
| M1 package opened, inventory reproducible | validated | — |
| M2 executable container analysed | validated | — |
| M3 lift pipeline proven on a synthetic ELF | validated | — |
| M4 native build of lifted code | planned | no compiler (KI-003), no runtime sources (KI-009) |
| M5 decrypted EBOOT lifted | validated | — |
| M6 runtime boot, first frame | planned | depends on M4 |
| M7 playable | planned | depends on M6 |

M4 and M5 are independent: lifting needs no compiler, and building needs no
further analysis. M5 finished first because the owner supplied the decrypted
image.

## Task log

| Date | Task | State | Evidence |
|---|---|---|---|
| 2026-11-14 | Install and validate Ghidra, JDK, Node, REA, Python stack | done | `scripts/verify-tools.ps1` → 6/6 OK |
| 2026-11-14 | Parse the retail package header | done | `pkg-info`: 46 items, `total_size` == file size |
| 2026-11-14 | Extract the package | done | 46 files, 551 MB |
| 2026-11-14 | Parse PARAM.SFO | done | `TITLE = After Burner Climax`, `TITLE_ID = NPUB30151` |
| 2026-11-14 | Parse the SELF container | done | entry `0x4CDF00`, 8 phdrs, `retail_encrypted: true` |
| 2026-11-14 | Characterise Sega FArc (both variants) | done | 2 + 101 records, gzip payloads |
| 2026-11-14 | Characterise CRI ADX audio | done | 23 files, 44.1 kHz, 1,898.9 s |
| 2026-11-14 | Probe the PSARC table of contents | blocked | 0/32 entries plausible → `opaque` |
| 2026-11-14 | Lift a synthetic PS3 ELF to C++ | done | 1 function → 1,117 lines |
| 2026-11-14 | Verify the owner-supplied decrypted ELF | done | `e_machine=21`, `e_entry=0x4CDF00`, SHA-256 recorded |
| 2026-11-14 | Load the real image | done | 11,827 OPDs → 11,338 functions, TOC `0x4ed088` |
| 2026-11-14 | Extract and resolve firmware imports | done | 207 imports, 14 libraries, 163 NIDs named |
| 2026-11-14 | Ghidra auto-analysis of the real image | done | 11,541 functions, 118,346 symbols, 358 s |
| 2026-11-14 | Lift the real image | done | 15,237 functions, 9m10s, 2 warnings |
| 2026-11-14 | Identify engine and middleware from strings | done | AM2 motion, AET, CRI 3.44.03, ENEPACK |
| 2026-11-14 | Compile the generated C++ | blocked | no compiler on the host |
| 2026-11-14 | Link against the runtime | blocked | runtime sources not in the binary release |

## Next steps, ordered by risk and dependency

1. **Install MSVC Build Tools, CMake and Ninja.** Unblocks M4. Acceptance: `cl`
   and `cmake --version` succeed.
2. **Obtain the toolkit runtime sources.** The binary release ships headers and
   `ps3recomp_runtime.lib` but not `ppu_load_elf`, `ppu_recomp_register`,
   `ppu_hle_init` or `ppu_run`; the upstream project template links them from
   `PS3RECOMP_DIR`. Acceptance: a project that resolves those symbols.
3. **Compile the 17 generated chunks.** Expect long compile times: 9.57 M lines.
   Acceptance: objects produced with no errors, or a documented list of the ones
   that fail.
4. **Boot to the first frame.** Acceptance: a captured frame, not a log line.
5. **Re-lift with Ghidra names.** 1,289 engine symbols are already extracted;
   feeding them through `--names` makes the generated code readable. Do this
   after the first successful build so the diff stays reviewable.
6. **Attack the `rom.psarc` TOC.** Needed before any asset conversion. The
   reader is now findable in the decrypted image rather than a guess.

## What was deliberately not done

- No function names, addresses or import lists were invented. Every figure in
  the documentation traces to a command in the validation log.
- No stub was written for a library that the runtime already implements.
- The generated C++ was not hand-edited; it is regenerated on every lift.
- No game bytes were committed. The decrypted image lives in `work/game/`,
  which is git-ignored.

## Risks

| Risk | Impact | Mitigation |
|---|---|---|
| 9.57 M lines may exceed compiler limits | build fails in unexpected ways | split further with `--chunks`; MSVC `/bigobj` |
| `cellSpurs` is only Partial upstream | SPU jobs may not run | isolate the `efc_smoke_job` path early |
| `rom.psarc` TOC stays unreadable | asset conversion impossible | research task, not a code blocker |
| Cg/RSX translation coverage | rendering will not match | start from the shared runtime's RSX layer |
| 2 lift warnings at segment end | possible truncated tail functions | inspect `func_00380E00` and `func_004B6F60` |
