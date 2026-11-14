# Known issues

Each entry records the exact error observed, the cause, and the workaround or
the reason none exists.

## KI-001 — EBOOT payload is encrypted

**Severity:** blocking (M5)

**Observed.** `skyclimax self-info` reports `retail_encrypted: true`. The first
64 KiB of segment 0 has an entropy of 7.9973 bits/byte and contains no readable
instructions. `unfself.py --info` prints `key_revision : 0x0001 (RETAIL -
encrypted)`.

**Cause.** Retail SELF segments are AES-encrypted with a per-title key that is
not derivable from the package.

**Workaround.** None implemented, by design (ADR-0002, ADR-0004). The owner must
supply either the title key or an executable dumped from a running copy.

**Do not** substitute a heuristic disassembly of the ciphertext for real
analysis; it produces plausible-looking garbage.

## KI-002 — `rom.psarc` table of contents is opaque

**Severity:** blocking (asset pipeline)

**Observed.** Header parses; `toc_state` is `opaque`, with 0 of 32 probed
entries consistent with the documented layout.

**Cause.** Unknown. The region is not plaintext, not zlib and not deflate; its
entropy (~7.2 bits/byte) rules out both a naive read and simple AES.

**Workaround.** None. `skyclimax.psarc` returns an empty entry list instead of
guessing.

## KI-003 — No C/C++ toolchain on this host

**Severity:** resolved

**Observed.**

```text
cl      MISSING
cmake   MISSING
ninja   MISSING
gcc     MISSING
clang   MISSING
```

**Cause.** The workstation has no Visual Studio Build Tools installation.

**Fix applied.** Visual Studio Build Tools 2022 (17.14.45, MSVC 14.44.35207,
SDK 10.0.26100.0) was installed, and LLVM 23.1.5 provides clang-cl, which is the
only compiler that accepts the generated header's `__atomic_*` and
`__builtin_bswap*` usage. `scripts/build.py` drives clang-cl and Ninja directly.

**Verified.** All 24 PPU translation units and 5 SPU units compile with zero
errors, and the link produces `build/SkyClimax.exe` (295.6 MB).

## KI-004 — Ghidra 12.2 rejects JDK 21

**Severity:** resolved

**Observed.**

```text
WARNING: JAVA_HOME environment specifies unsupported java version
ERROR: Unable to prompt user for JDK path, no TTY detected.
```

**Cause.** `application.java.min=25`.

**Fix.** Install Temurin 25 and export `JAVA_HOME` to it. Verified: headless
banner prints, and a PPC64 ELF imports with language
`PowerPC:BE:64:default`.

## KI-005 — REA's Windows Ghidra provider is PE-only

**Severity:** limitation (analysis workflow)

**Observed.** `rea capabilities` reports, verbatim: *"Windows Ghidra P0 accepts
native x86, x86-64, ARMNT (Thumb-2) and ARM64 PE applications and DLLs, DOS MZ
images, and explicitly selected raw 6502 images; managed, hostile, sensitive,
and mutable-path targets are unsupported."*

**Cause.** The Windows bridge targets native PE binaries.

**Workaround.** Drive Ghidra headless directly for PPU ELF analysis (ADR-0005),
or run REA on Linux/macOS where its Ghidra provider handles ELF.

## KI-006 — npm does not create a `.bin` shim under `--prefix`

**Severity:** resolved

**Observed.** `.tools/rea/node_modules/.bin/rea: No such file or directory`
after a successful install.

**Cause.** `npm install --prefix` without a `package.json` in the prefix does not
link binaries.

**Fix.** Invoke the entry script directly:
`node .tools/rea/node_modules/rea-agents/scripts/rea.mjs`.

## KI-007 — `pkg_extract.py` needs `pycryptodome` for acceptable speed

**Severity:** resolved

**Observed.** Without `pycryptodome`, the extractor falls back to a pure-Python
AES implementation and a 551 MB package takes an extremely long time.

**Fix.** `pip install pycryptodome` in `.venv` (it is part of the dev extras).
The extractor prints `(pycryptodome)` when the fast path is active.

## KI-008 — PKG `info_size` does not match `item_count`

**Severity:** cosmetic (open question)

**Observed.** `info_offset = 192`, `info_size = 8`, `item_count = 46`. A flat
`{u32 id, u32 size}` table of 46 entries would be 368 bytes, and would extend
past `data_offset = 384`.

**Status.** Unresolved. The header fields are reported raw; entry enumeration is
delegated to the ps3recomp extractor, whose 46-file result cross-validates
`item_count`.

## KI-009 — the binary release omits the runtime sources

**Severity:** resolved

**Observed.** `lib/ps3recomp_runtime.lib` exports HLE implementations
(`cellAudioInit`, `cellGcmSys` helpers, …) but none of the boot entry points.
Searching the library for `load_elf` and `run` returns nothing, and the upstream
template's `main.cpp` states that `ppu_load_elf`, `ppu_recomp_register`,
`ppu_hle_init`, `ppu_sysprx_register`, `ppu_fs_register`, `lv2_init_syscalls`
and `ppu_run` are "compiled into this project from `PS3RECOMP_DIR`".

**Cause.** v0.19.0 is published as a binary release; the runtime sources and the
`templates/project/` tree live in the upstream repository, not in the archive.

**Fix applied.** The upstream repository was cloned into
`.vendor/ps3recomp-src` and checked out at `ae92407bb1d899e3d32143e360fe6e6d4d8fa1b5`
— the exact commit recorded in the release's `VERSION.txt`. It provides
`runtime/ppu/ppu_loader.cpp`, `ppu_hle.cpp`, `ppu_fs.cpp`, `ppu_sysprx.cpp`,
`libs/*.c` and `templates/project/`, which the template's `CMakeLists.txt`
consumes through `PS3RECOMP_DIR`.

**Verified.** `git log -1` reports `ae92407bb1d899e3d32143e360fe6e6d4d8fa1b5`
and `runtime/ppu/` contains the four boot sources. Linking is still untested
because the compiler is missing (KI-003).

## KI-010 — the title stalls because the GCM queue handler is never called

**Severity:** blocking (M7)

**Observed.** After four `SetConvertAndFlip` calls the title blocks forever in
`sys_event_queue_receive` on the queue it created itself:

```text
[evt] queue_create -> id=1 key=0x8000CAFE02460300 size=2
[cellGcmSys] SetQueueHandler(00000000004D9558)
[WAIT] event_queue_receive(q=1 timeout=9000000) tid=3 cia=0x004E3480 lr=0x002C698C
```

The guest function at `0x002C68A0` builds the key `0x8000CAFE02460300`, creates
the queue, and then waits in a 100-iteration loop with a 9 s timeout, destroying
the queue afterwards. It is waiting for the handler it registered through
`cellGcmSetQueueHandler` (NID `0x0A862772`).

**Cause.** `libs/video/cellGcmSys.c` stores the argument in a *host* function
pointer (`CellGcmQueueHandler`) and never invokes it. The upstream comment at the
FIFO-circling heuristic even states that the "SetQueueHandler / context-switch
path" is not modelled. The argument the game passes is a guest OPD, so calling it
as a host pointer would jump into guest code.

**Hypothesis tested and falsified.** `tools/patches/apply.py` patch 0001 keeps the
value as a 32-bit guest OPD and dispatches it through `g_ps3_guest_caller` at the
same points the flip handler fires. It was applied, the runtime was rebuilt from
source, and the title behaved identically: 612 `event_queue_receive` calls in
100 s, still stalled. The patch has been reverted and the script kept only as a
record of the experiment.

**What this rules out.** The queue handler is not what wakes that wait. The wait
returns quickly rather than after its nominal timeout (612 calls in 100 s cannot
be 9 s each), so the receive is most likely failing immediately and the title is
retrying, which points at the queue itself or at the producer that should push to
it — not at the GCM callback.

**Next probe.** Log the return value of `sys_event_queue_receive` for `q=1`, and
log every `sys_event_queue_push` with its target queue id, so the producer that
never runs can be identified by name rather than guessed.
