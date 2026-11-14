# Status and task log

Last updated: 2026-11-14.

## Current position

**Milestone reached: M6 — the recompiled executable boots and presents frames.**
It is not playable: the title loads its archives, brings up the renderer and then
sits in an idle wait, and the only device available on this host is the software
rasterizer.

| Milestone | State | Note |
|---|---|---|
| M0 toolchain installed and validated | validated | clang-cl 23.1.5 + MSVC 14.44 + Ninja |
| M1 package opened, inventory reproducible | validated | 46 files |
| M2 executable container analysed | validated | SELF + ELF layout |
| M3 lift pipeline proven on a synthetic ELF | validated | 1 function |
| M4 native build of lifted code | validated | 24 PPU TUs + 5 SPU TUs → 295.6 MB exe |
| M5 decrypted EBOOT lifted | validated | 15,237 functions |
| M6 runtime boot, first frame | validated | frames presented; content not verified |
| M7 playable | planned | blocked on the idle wait and on GPU availability |

## Task log

| Date | Task | State | Evidence |
|---|---|---|---|
| 2026-11-14 | Install and validate the toolchain | done | `scripts/verify-tools.ps1` → 6/6 OK |
| 2026-11-14 | Extract and analyse the package | done | 46 files; `PARAM.SFO`, FArc, ADX, PSARC readers |
| 2026-11-14 | Verify the owner-supplied decrypted ELF | done | `e_machine=21`, `e_entry=0x4CDF00`, SHA-256 recorded |
| 2026-11-14 | Load the real image | done | 11,338 functions, 207 imports / 14 libraries |
| 2026-11-14 | Ghidra auto-analysis | done | 11,541 functions, 118,346 symbols, 358 s |
| 2026-11-14 | Lift the real image | done | 15,237 functions, 9,571,078 lines |
| 2026-11-14 | Compile the lifted code | done | 24 TUs, 0 errors, `SkyClimax.exe` 295.6 MB |
| 2026-11-14 | Lift the embedded SPU images | done | 3 images, fingerprint `9470BA4123AAAB63` |
| 2026-11-14 | Boot to first frame | done | D3D12 init, `SetConvertAndFlip` ×4, `rom.psarc` TOC read |
| 2026-11-14 | Reach gameplay | blocked | idles in `event_queue_receive` |

## What the boot log proves

Quoted from `work/reports/run2.log`:

```text
[ppu] loaded 2 PT_LOAD segments, entry OPD 0x004CDF00
[boot] dispatching entry OPD 0x004CDF00 (stack top 0x0FF00000)
[ppu] run: code 0x00010230, toc 0x004ED088, sp 0x0FEFFF20
[D3D12] Initialization complete (1280x720, 2 buffers, pipeline=ready)
[rsx] D3D12 backend init OK -- window open
[fs] open '/dev_bdvd/PS3_GAME/USRDIR/ps3/rom.psarc' -> fd 3
[fs] read fd=3 nbytes=48 -> 48 (magic=50534152, total=48)
[fs] read fd=3 nbytes=31676 -> 31676
[fs] open '/dev_bdvd/PS3_GAME/USRDIR/ps3/shader_cg.farc' -> fd 4
[cellResc] SetConvertAndFlip(src=260046848) -> flip
```

`50534152` is `PSAR`: the game opens its own 407 MB archive and reads the table
of contents that this project could not parse statically. The runtime's file
layer, the RSX command stream, `cellResc` and `cellSpurs` are all live.

## Known limitations at this milestone

- **No hardware GPU on this host.** D3D12 falls back to WARP ("Microsoft Basic
  Render Driver"), so nothing here says anything about rendering performance or
  correctness.
- **No audio device.** `cellAudio` logs `Failed to get default audio endpoint`
  and continues silently.
- **The title idles.** After the flips it blocks in `event_queue_receive`
  (`cia=0x004E3480`), which is the cellSysutil event loop waiting for an event
  that never arrives.
- **The PPU code is built `/Od`.** This host has 7.9 GB RAM and a 600k-line TU
  at `/O1` needs ~2.5 GB and ~10 minutes; the build pages out badly. Rebuild
  with `scripts/build.py --optimize` on a machine with more memory.

## Next steps, ordered by risk and dependency

1. **Find why the event loop never receives.** Inspect the guest callback
   registered by `cellSysutilRegisterCallback` (`func=0x004D7060`) and whether
   the runtime ever fires slot 0. Acceptance: the log advances past
   `event_queue_receive` without a timeout.
2. **Verify frame content.** Capture the presented surface and compare it with a
   reference run. Acceptance: a non-black frame with the title's own output.
3. **Run on a machine with a GPU** so D3D12 uses hardware and the RSX path is
   exercised for real.
4. **Rebuild optimised** once the title advances, to see whether `/Od` is
   itself the cause of the stall.
5. **Re-lift with Ghidra names** (1,289 engine symbols are already extracted) so
   the generated code is readable while debugging step 1.
