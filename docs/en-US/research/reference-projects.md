# Reference projects

Metadata below was retrieved from the GitHub API on 2026-11-14 and is quoted,
not inferred. Each project was assessed for architecture, not copied.

| Repository | Primary language | Last push | Description (verbatim) |
|---|---|---|---|
| `sp00nznet/ps3recomp` | C | 2026-11-06 | Static recompilation runtime libraries for PlayStation 3 titles. |
| `n0madic/Soulcalibur2HD-recomp` | C | 2026-10-26 | Soulcalibur II HD native recompilation |
| `soyjxck/dod3-recomp` | C++ | 2026-11-03 | Drakengard 3 (PS3) static recompilation using ps3recomp |
| `whompay/inFAMOUSreborn` | C | 2026-11-12 | (no description) |
| `WK2D/White-Knight-Chronicles-2-Recomp` | C++ | 2026-10-22 | Native C/C++ recompilation for White Knight Chronicles II (PS3). |
| `SulphurS16/ACFA-Port` | C++ | 2026-11-04 | Unofficial native Windows port of ARMORED CORE for Answer (PS3), built from your own copy of the game. |
| `SulphurS16/AC4-Port` | C++ | 2026-10-29 | Unofficial native Windows port of ARMORED CORE 4 (PS3), built from your own copy of the game. |
| `kastieloficial/RE-Code-Veronica-PS3-HD-Recomp-PC` | C | 2026-11-13 | Resident Evil Code: Veronica X HD - PS3 static recompilation port (hobby, no game data) |
| `timboat/demons-souls-recomp` | Python | 2026-11-13 | Native Windows port of Demon's Souls (PS3, BLUS-30443) via ps3recomp static recompilation. |
| `morluto/rea` | TypeScript | 2026-11-14 | Reverse engineer anything with agents, from app behavior down to native binaries. |

## What the metadata already tells us

1. **Two projects name ps3recomp as their engine** (`dod3-recomp`,
   `demons-souls-recomp`). Combined with `ps3recomp` itself being the C runtime
   that the other ports link against, the ecosystem has converged on one
   backend rather than one recompiler per game.
2. **The host language is C or C++** in eight of nine ports, which matches a
   pipeline whose output is generated C++ compiled by a native toolchain.
3. **Python appears as the orchestration language** (`demons-souls-recomp`),
   consistent with the ps3recomp tools being Python scripts that drive a
   CMake build.
4. **All repositories are active** (last push within the last month at fetch
   time), so the tooling is still moving. Pinning versions is therefore not
   optional for reproducibility.

## Reusable techniques

- **OPD-driven function boundaries.** ps3recomp documents that the `.opd`
  section gives an authoritative function list, which is far more reliable than
  scanning for prologues. SkyClimax adopts this: the entry point of
  `EBOOT.BIN` is `0x4CDF00`, inside the data segment, which is exactly the OPD
  layout this technique assumes.
- **HLE modules keyed by NID.** Every port needs `cellGcmSys`, `cellAudio`,
  `cellPad`, `cellFs`, `cellSysutil` and friends. Implementing them once, keyed
  by the 32-bit NID, is the only tractable approach.
- **Bring-your-own-game distribution.** Every port ships code only. SkyClimax
  follows the same rule: no proprietary bytes in the repository.
- **Synthetic smoke ELF as a pipeline test.** ps3recomp ships
  `make_smoke_elf.py`; SkyClimax uses it to prove the lift path works before the
  real binary is available.

## Techniques deliberately not adopted

- **Per-game hand-written graphics backends.** `ACFA-Port` and `AC4-Port` are
  ports of two games from one engine; the shared work is the engine layer, not
  a bespoke renderer per title. SkyClimax keeps the RSX translation in the
  shared runtime and keeps game-specific code out of it.
- **Runtime interpretation of PPU code.** That is an emulator, not a static
  recompilation, and it contradicts the project goal.
- **Committing decrypted assets or keys.** No reference project does this, and
  doing so would make the repository unpublishable.

## Open question carried forward

None of the reference projects documents an After Burner Climax port, and the
title is a 2010 Sega AM2 arcade conversion rather than a PhyreEngine or Unreal
title. Its middleware stack (Sega `FArc`, CRI `ADX`, Cg shaders) therefore has
to be characterised from the package itself, which is what
[the asset analysis](../analysis/assets.md) does.
