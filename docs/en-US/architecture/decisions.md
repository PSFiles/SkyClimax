# Decision log

Each record states the decision, the evidence behind it, and what would make it
wrong. New records are appended; existing ones are not rewritten.

## ADR-0001 — Use ps3recomp as the recompiler backend

**Status:** accepted

**Context.** Nine reference projects exist; two name ps3recomp explicitly as
their engine, and ps3recomp itself ships a loader, lifter, stub generator and a
Windows runtime library.

**Decision.** SkyClimax vendors ps3recomp v0.19.0 and adds only game-specific
analysis and compatibility code.

**Consequences.** Upstream bugs are inherited and must be worked around with
documented patches. In exchange the project starts at a working lifter instead
of at a blank file.

**Falsified if** ps3recomp cannot express a required construct (for example a
PPU instruction it does not lift) and the gap cannot be closed by a patch.

## ADR-0002 — Never guess at encrypted content

**Status:** accepted

**Context.** `EBOOT.BIN` segments and the `rom.psarc` table of contents are both
opaque. It is easy to produce plausible-looking function lists or archive
indexes that are entirely fictional.

**Decision.** Parsers report an explicit state (`toc_state: "opaque"`) and
return empty results rather than heuristics. Documentation states the blocker
and the evidence (entropy figures, failed layout probes).

**Consequences.** The project looks less complete than a fabricated version
would, and that is the point: every number in the docs can be traced to a
command.

**Falsified if** never — this is a process rule, not a technical hypothesis.

## ADR-0003 — Keep the en-US and pt-BR trees byte-parallel

**Status:** accepted

**Context.** Bilingual documentation rots immediately unless a machine checks it.

**Decision.** `scripts/check_docs_parity.py` compares file sets, heading order,
code-block count, code-block bodies for code languages, and relative links, and
validates the index in `docs/README.md`. CI runs it on every push.

**Consequences.** A translation cannot be "mostly done": a missing heading fails
the build.

## ADR-0004 — Do not ship keys or decrypted payloads

**Status:** accepted

**Context.** The repository is public.

**Decision.** `.gitignore` excludes `*.pkg`, `*.rap`, `*.elf`, `*.self`,
`work/`, `.tools/`, `.vendor/` and any `keys` file. The documentation explains
how the owner produces a decrypted image locally.

**Consequences.** A fresh clone cannot run the game; it can reproduce every
analysis step given the retail package.

## ADR-0005 — Treat REA as an orchestration layer, not a PS3 analyser

**Status:** accepted

**Context.** REA 6.9.0's own capability report states, verbatim: *"Windows Ghidra
P0 accepts native x86, x86-64, ARMNT (Thumb-2) and ARM64 PE applications and
DLLs, DOS MZ images, and explicitly selected raw 6502 images"*. A PS3 PPU
executable is a big-endian PPC64 ELF, which is not in that set.

**Decision.** Ghidra is driven directly through `analyzeHeadless` for PPU work.
REA stays installed and is used for evidence bookkeeping and for analysis on
hosts whose Ghidra provider accepts ELF.

**Consequences.** The project does not depend on REA for its critical path,
which is also why it keeps working if REA changes its admission policy.

**Falsified if** REA's Windows provider starts accepting ELF/PPC64, in which
case ADR-0005 can be superseded.

## ADR-0006 — FArc variant selection is a validated hypothesis, not a fact

**Status:** accepted

**Context.** Only two FArc samples exist in the package, and they differ in the
case of the fourth magic byte and in record width.

**Decision.** Select the record layout from the magic byte, then validate every
record against the file bounds; raise on mismatch instead of truncating.

**Consequences.** If a third variant appears, the parser fails loudly rather
than mis-parsing silently.

## ADR-0007 — Audio is treated as data, not as SPU code

**Status:** proposed

**Context.** All 23 music/effect streams are CRI ADX with self-describing
headers; voice is a CRI AFS bank. None of that requires Cell SPU execution if
the host decodes the streams itself.

**Decision (proposed).** Decode ADX/AFS on the host and expose them through the
`cellAudio` HLE surface, rather than lifting the game's SPU audio jobs.

**Consequences.** Requires a working ADX decoder on the host, which is well
understood. It does not help if the game also uses SPU for mixing effects that
are not present in the ADX data.

**Falsified if** the game drives audio through SPU jobs whose output is not a
straight ADX stream.
