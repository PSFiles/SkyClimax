# Status and task log

Last updated: 2026-11-14.

## Current position

**Milestone reached: M3 — the lift pipeline is proven on a synthetic PS3 ELF.**
The project is experimental. No recompiled game code exists, and nothing has
been compiled.

| Milestone | State | Blocking issue |
|---|---|---|
| M0 toolchain installed and validated | validated | — |
| M1 package opened, inventory reproducible | validated | — |
| M2 executable container analysed | validated | payload encrypted |
| M3 lift pipeline proven on a synthetic ELF | validated | — |
| M4 native build of lifted code | planned | no C/C++ compiler (KI-003) |
| M5 decrypted EBOOT lifted | planned | no key (KI-001) |
| M6 runtime boot, first frame | planned | depends on M4 and M5 |
| M7 playable | planned | depends on M6 |

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
| 2026-11-14 | Import a PPC64 ELF into Ghidra | done | `PowerPC:BE:64:default`, import succeeded |
| 2026-11-14 | Lift a synthetic PS3 ELF to C++ | done | 1 function → 1,117 lines |
| 2026-11-14 | Decrypt the retail EBOOT | blocked | requires a title key or a decrypted dump |
| 2026-11-14 | Compile the generated C++ | blocked | no compiler on the host |

## Next steps, ordered by risk and dependency

1. **Obtain a decrypted `EBOOT.elf`.** Everything downstream is blocked on it.
   Highest risk, highest value. Acceptance: `e_machine = 21`,
   `e_entry = 0x4CDF00`, SHA-256 recorded.
2. **Install MSVC Build Tools, CMake and Ninja.** Unblocks M4 independently of
   step 1, and can be done in parallel. Acceptance: `cl` and `cmake --version`
   succeed, and the synthetic lift compiles.
3. **Lift the real image and count functions.** Acceptance: loader and lifter
   agree on the function count, and no `has no continuation` warnings remain.
4. **Group the firmware imports by library.** This determines the HLE scope and
   therefore the real schedule. Acceptance: a table of library → NID count in
   the compatibility matrix.
5. **Attack the `rom.psarc` TOC.** Needed before any asset conversion. Approach:
   look for the reader in the decrypted EBOOT rather than guessing the format.
6. **Translate the 101 Cg programs.** Only meaningful once the renderer runs.

## What was deliberately not done

- No function names, addresses or import lists were invented for the retail
  image. The payload is encrypted; reporting such data would be fabrication.
- No decryption keys were generated, guessed or embedded.
- No stub was written for a library that has not been observed in a real import
  table.
- No `tools/` directory was created, because no auxiliary tool beyond `scripts/`
  was needed; empty scaffolding is not progress.

## Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Decryption never becomes available | project cannot pass M2 | document the exact requirement; keep every other stage testable without it |
| `rom.psarc` TOC stays unreadable | asset conversion impossible | treat as a research task, not a blocker for code work |
| Cg/RSX translation coverage | rendering will not match | start from the shared runtime's RSX layer, not a bespoke renderer |
| SPU-heavy audio | audio path may need SPU execution | ADX is self-describing; prefer host decoding (ADR-0007) |
| Backend drift | recompiled output changes silently | pin ps3recomp by commit; patch rather than fork |
