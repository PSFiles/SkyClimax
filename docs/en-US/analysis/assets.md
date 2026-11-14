# Asset analysis

All figures come from the extracted package. Reproduce with:

```bash
python -m skyclimax inventory work/pkg --json work/reports/inventory.json
```

## Middleware stack

The package identifies its own middleware by file format, not by strings in a
binary we cannot read:

| Format | Evidence | Role |
|---|---|---|
| PSARC | `PSAR` magic, `zlib` compression, 218 TOC entries | main asset archive (407 MB) |
| Sega FArc | `FArc` / `FArC` magic | system and shader archives |
| CRI ADX | `0x8000` + `(c)CRI` | music and voice streams |
| CRI AFS | `AFS\0` magic | voice bank container |
| Cg | `.vp` / `.fp` entry names, gzip payloads | GPU programs |

## Sega FArc

Two variants appear in the same package, distinguished by the case of the fourth
magic byte:

| Variant | Record layout | Verified on |
|---|---|---|
| `FArc` | `cstring name, u32 offset, u32 size` | `SYSTEM.farc` (2 records) |
| `FArC` | `cstring name, u32 offset, u32 size, u32 uncompressed_size` | `shader_cg.farc` (101 records) |

In both variants the header field at `0x04` equals `first_data_offset - 8`, which
held for both samples (`0x2F - 8 = 0x27`, `0x116E - 8 = 0x1166`). Because only
two samples were available, `skyclimax.farc` treats the variant as a hypothesis
and validates every record against the file bounds instead of trusting it.

### Shader archive

`shader_cg.farc` holds 101 records, all gzip-compressed:

| Extension | Count | Interpretation |
|---|---|---|
| `.vp` | 46 | vertex programs |
| `.fp` | 55 | fragment programs |

Nine base names carry all permutations, for example `blinn_frag_cubemap`,
`blinn_frag_default`, `blinn_vert_default`, `deck_default`, `refrac_default`,
`sea_default`, `sea_nonref`, `sea_shadow`, `sky_default`.

Two consequences for the port:

- Shaders are **Cg compiled to PS3 microcode**, not GLSL or HLSL source. A
  translation layer (Cg/RSX microcode to HLSL/SPIR-V) is unavoidable; the
  RSX translation in ps3recomp is the component that must cover this.
- The permutation scheme (`blinn_vert_default.0100.fp`, `.0111.fp`, …) means
  shader variants are selected by a numeric key. The renderer must reproduce
  that key selection or lighting will be wrong even if every shader compiles.

## Audio

| Property | Value |
|---|---|
| ADX files | 23 (20 music + 3 effects/selector) |
| Total ADX duration | 1,898.9 s ≈ 31.6 min |
| Channels | mono and stereo |
| Sample rate | 44,100 Hz for all files |
| Encoding | 4-bit, version 3, block size 18 |
| Voice bank | `voice.afs`, 38,895,616 bytes |

The ADX headers parse deterministically, so the audio path can be validated
against the original stream lengths without decoding a single sample.

## Main archive: `rom.psarc`

The header parses cleanly:

| Field | Value |
|---|---|
| magic / version | `PSAR` / `0x00010004` |
| compression | `zlib` |
| header span | 31,708 bytes |
| TOC entry size / count | 30 / 218 |
| block size | 65,536 |

The table of contents, however, is **not readable with the documented layout**:

- 0 of 32 probed entries satisfy `block_index < file_size / block_size`;
- no ASCII entry names exist anywhere in the 31 KB header span;
- the region is neither a zlib stream nor deflate;
- its entropy is ~7.2 bits/byte, which is neither plaintext structure nor
  ciphertext.

`skyclimax.psarc` therefore reports `toc_state: "opaque"` and returns an empty
entry list. Guessing offsets here would silently corrupt every downstream
conclusion, so the tool refuses instead. This is the single largest unresolved
gap in the asset analysis: 96 % of the package payload is currently unindexed.

## Localisation

`USRDIR/string_array.bin` (35,472 bytes) and `USRDIR/lang/en/string_array.bin`
(26,944 bytes) begin with a table of big-endian `u32` offsets
(`0x00000CD0`, `0x00000CE0`, `0x00000CF0`, …), i.e. an offset array into a
string blob. Only the English tree is present in this package.

## What this implies for the port

1. **The renderer must speak Cg/RSX microcode.** There is no shader source to
   port by hand.
2. **Audio can be treated as data, not code.** ADX/AFS are self-describing; the
   host can decode them with a library instead of reimplementing Cell SPU audio.
3. **The asset pipeline blocks on `rom.psarc`.** Until its TOC is readable, the
   content of the largest archive — presumably models, textures and levels — is
   unknown, and no asset conversion work can start.
