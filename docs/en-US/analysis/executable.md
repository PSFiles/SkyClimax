# Executable analysis

Source: `USRDIR/EBOOT.BIN`, 5,656,176 bytes, extracted from the retail package.
Reproduce with:

```bash
python -m skyclimax self-info work/pkg/USRDIR/EBOOT.BIN
```

## Container

| Field | Value |
|---|---|
| magic | `SCE\0` |
| SELF version | 2 |
| key revision | 1 (retail, signed and encrypted) |
| header type | 1 |
| metadata size | 1,184 |
| header span | 2,688 (`0xA80`) |
| contained ELF size | 5,653,432 (`0x5643B8`) |
| program headers | 8 |
| section headers | 31 |

## Embedded ELF header

The ELF header is copied into the SELF header and is therefore readable even
though the segments are not:

| Field | Value | Meaning |
|---|---|---|
| class | 2 | ELF64 |
| data | 2 | big-endian |
| OSABI | `0x66` | PlayStation 3 |
| `e_type` | 2 | `ET_EXEC` — fixed load address, no relocations |
| `e_machine` | 21 | `EM_PPC64` |
| `e_entry` | `0x4CDF00` | OPD descriptor, not code |
| `e_phoff` | `0x40` | |
| `e_flags` | 0 | |

`ET_EXEC` is the easy case for static recompilation: the image loads at a fixed
address, so no relocation processing is required for the main executable.

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

Three observations that drive the architecture:

1. **The entry point sits in the data segment.** `0x4CDF00` falls inside
   program header 1 (`0x4C0000`–`0x4E554A8`), which is `R+W` and not
   executable. That is the classic OPD layout: the entry is an 8-byte
   `{code, TOC}` descriptor, so the loader must resolve it before running.
   ps3recomp's loader does exactly this and reports
   `entry (OPD) -> code, toc`.
2. **BSS is 17.3 MB** (`0x11A3994`) against 727 KB of initialised data. Any
   host implementation must reserve the full `memsz`, not just `filesz`.
3. **Program header 7 is the PS3 parameter segment** (`p_type 0x60000002`),
   which is where the firmware import table lives. In a decrypted image this is
   the authoritative source of `(library, NID, stub address)` triples.

## Encryption state

All payload segments are AES-encrypted. Evidence: the first 64 KiB of segment 0
has an entropy of **7.9973 bits/byte**, and no readable instruction stream or
string table appears anywhere in the segment data. The plaintext ends at the
SELF metadata boundary (`0xA80`).

Consequences, stated plainly:

- **No function count, no import list and no symbol names can be reported.**
  Anything of that kind in this repository would be fabricated.
- The `.opd`-driven function discovery that the reference projects rely on
  cannot run until the image is decrypted.
- Ghidra cannot analyse the file as-is; it would import 5.6 MB of noise.

## What unblocks this

In descending order of preference:

1. **User-supplied keys.** A `keys` file for `scetool`-style decryption, or the
   klicensee plus the title's app key. The 16-byte `.rap` next to the package is
   a klicensee for EDAT payloads and is not sufficient on its own for the SELF.
2. **A decrypted dump produced by the owner.** RPCS3 can dump a decrypted
   executable when loading the title; the resulting ELF is byte-identical to the
   `PT_LOAD` images and is what ps3recomp expects.
3. **Dynamic extraction.** Running the title under an emulator with memory
   dumps yields the same image, at the cost of a much longer procedure.

SkyClimax does not attempt to defeat the protection and does not embed keys.
The decrypted image is a local artefact and is git-ignored.

## Cross-check against the loader

`ppu_loader.py` is the reference implementation of this parsing. Run against a
synthetic PS3 ELF it reports:

```text
e_type           : 2 (EXEC)
entry (OPD)      : 0x20000 -> code 0x10000, toc 0x20d00
load segments    : 2
```

That is the same shape as the real executable, which is why the smoke test in
[the build guide](../build/build.md) is a meaningful rehearsal rather than a toy.
