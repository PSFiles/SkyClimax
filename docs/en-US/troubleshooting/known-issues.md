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

**Severity:** blocking (M4)

**Observed.**

```text
cl      MISSING
cmake   MISSING
ninja   MISSING
gcc     MISSING
clang   MISSING
```

**Cause.** The workstation has no Visual Studio Build Tools installation.

**Workaround.** Install VS Build Tools 2022 with "Desktop development with C++".
Until then the lifted C++ is verified structurally (non-empty, one function per
guest function, expected prologue/epilogue helpers present) but never compiled.

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
