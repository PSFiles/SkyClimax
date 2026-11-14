# Package analysis

Source: `UP0177-NPUB30151_00-AFTERBURNERCMX00.pkg`, 551,772,592 bytes, supplied
locally by the project owner. No package bytes are stored in the repository.

Reproduce with:

```bash
python -m skyclimax pkg-info UP0177-NPUB30151_00-AFTERBURNERCMX00.pkg
```

## Header

| Field | Value | Note |
|---|---|---|
| magic | `7f 50 4b 47` | `\x7fPKG` |
| revision | `0x80000001` | retail PS3 package |
| content ID | `UP0177-NPUB30151_00-AFTERBURNERCMX00` | matches the file name |
| item count | 46 | equals the number of extracted files |
| total size | 551,772,592 | equals the file size on disk |
| data offset | 384 | |
| data size | 551,772,112 | |

The `info_offset`/`info_size` pair at `0x08`/`0x0C` reads `192`/`8`, which does
not agree with `item_count × 8 = 368` for a flat `{u32 id, u32 size}` table.
That discrepancy is recorded as unresolved rather than explained away; entry
enumeration is delegated to the tested ps3recomp extractor, whose file count
cross-validates `item_count`.

## Extracted tree

| Path | Bytes | Kind |
|---|---|---|
| `PARAM.SFO` | 1,040 | system metadata |
| `PS3LOGO.DAT` | 5,120 | boot logo |
| `ICON0.PNG` | 59,468 | icon |
| `ICON1.PAM` | 1,974,272 | animated icon |
| `PIC0.PNG` | 204,415 | background |
| `PIC1.PNG` | 1,929,465 | background |
| `USRDIR/EBOOT.BIN` | 5,656,176 | encrypted SELF |
| `USRDIR/chkboot.edat` | 25,712 | EDAT payload |
| `USRDIR/lang/en/string_array.bin` | 26,944 | localisation |
| `USRDIR/ps3/SYSTEM.farc` | 791,247 | Sega FArc |
| `USRDIR/ps3/rom.psarc` | 407,077,221 | PSARC, 96 % of the payload |
| `USRDIR/ps3/shader_cg.farc` | 200,315 | Cg shader archive |
| `USRDIR/rom/adx/*.adx` | 20 files | CRI ADX music |
| `USRDIR/rom/adx/voice.afs` | 38,895,616 | CRI AFS voice archive |
| `USRDIR/string_array.bin` | 35,472 | localisation |
| `TROPDIR/NPWR00981_00/TROPHY.TRP` | 671,472 | trophies |

## System metadata

`PARAM.SFO` decodes to:

| Key | Value |
|---|---|
| `TITLE` | `After Burner Climax` |
| `TITLE_ID` | `NPUB30151` |
| `CATEGORY` | `HG` (installed to HDD) |
| `VERSION` | `01.00` |
| `APP_VER` | `01.00` |
| `PS3_SYSTEM_VER` | `03.0000` |
| `PARENTAL_LEVEL` | `4` |
| `BOOTABLE` | `1` |

`PS3_SYSTEM_VER 03.0000` means the title targets firmware 3.00, i.e. the
pre-3.41 syscall surface. That matters later: the HLE layer must cover the
3.00-era `sysPrxForUser` exports, not a modern firmware's.

## Reproduce the extraction

```bash
python .vendor/ps3recomp/tools/pkg_extract.py UP0177-NPUB30151_00-AFTERBURNERCMX00.pkg work/pkg
```

The extractor decrypts with the public `PS3_GPKG` AES-CTR key and needs no
per-title RAP file. The `.rap` supplied alongside the package is 16 bytes — a
raw klicensee — and is **not** required for this step. It is only relevant for
EDAT payloads such as `chkboot.edat`.
