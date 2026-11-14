# Tooling

Every version below was installed from an official source and exercised on this
machine. Anything that could not be installed is listed in
[known issues](../troubleshooting/known-issues.md) instead of being claimed as
available.

## Pinned versions

| Tool | Version | Source | Verification command | Result |
|---|---|---|---|---|
| Ghidra | 12.2 (build 2026-10-16) | GitHub release `Ghidra_12.2_build` | `support/analyzeHeadless` | Usage banner printed, exit 1 |
| Temurin JDK | 25.0.5+8 | Adoptium API, `latest/25/ga` | `bin/java -version` | `openjdk version "25.0.5"` |
| Node.js | 24.22.3 | nodejs.org `dist/v24.22.3` | `node --version` | `v24.22.3` |
| Python | 3.13.14 (venv) | local interpreter | `python -V` | `Python 3.13.14` |
| capstone | 5.0.7 | PyPI | `capstone.__version__` | `5.0.7` |
| pyelftools | 0.33 | PyPI | `elftools.__version__` | `0.33` |
| pycryptodome | 4.4.0 | PyPI | `Crypto.__version__` | `4.4.0` |
| LIEF | 1.0.0 | PyPI | `lief.__version__` | `1.0.0-d05b3499b` |
| ps3recomp | 0.19.0 | provided archive | `VERSION.txt` | `commit ae92407b…`, `win-x64` |
| VS Build Tools | 17.14.45 (MSVC 14.44.35207) | manual install | `vswhere -latest` | `C://Program Files (x86)\Microsoft Visual Studio\2022\BuildTools` |
| Windows SDK | 10.0.26100.0 | ships with Build Tools | directory listing | `10.0.26100.0` |
| LLVM / clang-cl | 23.1.5 | GitHub release `llvmorg-23.1.5` | `clang-cl --version` | `clang version 23.1.5` |
| Ninja | ships with Build Tools | — | `ninja --version` | used via `scripts/build.py` |

## Ghidra requires JDK 25, not JDK 21

Ghidra 12.2 declares `application.java.min=25` in
`Ghidra/application.properties`. Pointing `JAVA_HOME` at a JDK 21 installation
fails with:

```text
WARNING: JAVA_HOME environment specifies unsupported java version
ERROR: Unable to prompt user for JDK path, no TTY detected.
```

The project therefore pins JDK 25 and exports `JAVA_HOME` explicitly before
every Ghidra invocation.

## REA

REA is distributed as the npm package `rea-agents`. Version 6.9.0 declares:

```json
{ "node": "^22.23.4 || ^24.22.1 || >=26.12.1" }
```

The Node.js bundled with the workstation is 22.22.2, which does **not** satisfy
that range, so Node 24.22.3 is installed inside `.tools/` and prepended to
`PATH` for REA only. See [known issues](../troubleshooting/known-issues.md) for
the installation status of this session.

## ps3recomp

`ps3recomp` v0.19.0 is the recompiler backend. It is not vendored into git
because it is a binary release; `scripts/install-tools.ps1` fetches it into
`.vendor/`. Its own `VERSION.txt` reports:

```text
ps3recomp v0.19.0
platform: win-x64
commit:   ae92407bb1d899e3d32143e360fe6e6d4d8fa1b5
status:   renders and runs recompiled titles (D3D12)
```

The tools used by SkyClimax are `pkg_extract.py`, `ppu_loader.py`,
`ppu_lifter.py`, `ppu_disasm.py`, `generate_stubs.py`, `ghidra_analyze.py` and
`unfself.py`.

## Why clang-cl and not cl.exe

The generated `ppu_recomp.h` uses `__atomic_load_n`, `__atomic_store_n`,
`__builtin_bswap32/64` and `__builtin_expect` unconditionally. `cl.exe` has no
equivalent, and the header is machine-generated, so it cannot be patched by
hand. The toolkit's own CI compile-checks the Windows path with clang-cl, which
is therefore the supported compiler here. MSVC still supplies the headers,
libraries and `link.exe`; clang-cl is only the front end.

## Why CMake is not used

CMake's compiler probe invokes `reg.exe` to query the Visual Studio
installation. That program is blocked by this environment's program blacklist,
and the block cannot be approved from a command. Rather than route around a
security control, the build is driven by `scripts/build.py`, which locates the
toolchain, emits `build/build.ninja` for the 24 translation units and runs
Ninja. `src/port/CMakeLists.txt` is kept for hosts where CMake is usable.

See [build](../build/build.md) for the procedure.
