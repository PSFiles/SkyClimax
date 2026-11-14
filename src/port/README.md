# Port project

The runner for the recompiled title.

| File | Origin |
|---|---|
| `main.cpp` | ps3recomp v0.19.0 `templates/project/main.cpp`, commit `ae92407b`, unmodified |
| `stubs.cpp` | ps3recomp v0.19.0 `templates/project/stubs.cpp`, commit `ae92407b`, unmodified |
| `config.toml` | ps3recomp v0.19.0 `templates/project/config.toml`, unmodified (reference only; nothing reads it yet) |
| `CMakeLists.txt` | the same template, adapted: project name, and defaults pointing at this repository's `.vendor/ps3recomp-src` and `generated/` |

The upstream template is published by sp00nznet/ps3recomp for exactly this
purpose; see that project's licence. `main.cpp` is the runner and is
game-agnostic. `stubs.cpp` is where game-specific overrides go, and it is
currently the empty version — this title has needed none yet.

## Building here

Do **not** use `CMakeLists.txt` on this host: CMake's compiler probe invokes
`reg.exe`, which the sandbox blocks. Use the repository build driver instead:

```bash
python scripts/build.py --jobs 2
```

It emits `build/build.ninja` for the same translation units and runs Ninja with
clang-cl. `CMakeLists.txt` is kept for hosts where CMake is usable.

## Running

```bash
./build/SkyClimax.exe work/game/PS3_GAME/USRDIR/EBOOT.elf
```

The runner derives `PS3_VFS_ROOT` by stripping three path components from the
ELF path, so the disc tree must look like:

```text
work/game/PS3_GAME/USRDIR/EBOOT.elf
work/game/PS3_GAME/USRDIR/ps3/rom.psarc
work/game/dev_hdd0/home/00000001/trophy/NPUB30151/
```
