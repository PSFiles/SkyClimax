#!/usr/bin/env python3
"""Build the recompiled SkyClimax executable with clang-cl + Ninja.

CMake cannot be used on this host: its compiler probe shells out to ``reg.exe``,
which the sandbox blocks. This driver does the same job without it — it locates
the MSVC and LLVM installations, emits a ``build.ninja`` for the exact
translation units the port needs, and runs Ninja.

Toolchain layout it expects (all created by ``scripts/install-tools.ps1`` except
the Visual Studio part, which is a manual install):

    .tools/llvm-23/bin/clang-cl.exe
    <VS>/VC/Tools/MSVC/<ver>/...
    C:/Program Files (x86)/Windows Kits/10/...

Usage:
    python scripts/build.py --configure-only
    python scripts/build.py --jobs 8
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "build"
OBJ = BUILD / "obj"

#: The PPU boot scaffold. These include the per-game ppu_recomp.h, so they can
#: only be compiled against this particular lift — they are not in the runtime
#: library.
SCAFFOLD = [
    ".vendor/ps3recomp-src/runtime/ppu/ppu_loader.cpp",
    ".vendor/ps3recomp-src/runtime/ppu/ppu_hle.cpp",
    ".vendor/ps3recomp-src/runtime/ppu/ppu_fs.cpp",
    ".vendor/ps3recomp-src/runtime/ppu/ppu_sysprx.cpp",
]

#: Port-owned translation units.
PORT = ["src/port/main.cpp", "src/port/stubs.cpp"]

INCLUDE_DIRS = [
    "generated",
    ".vendor/ps3recomp-src/include",
    ".vendor/ps3recomp-src/runtime/ppu",
    ".vendor/ps3recomp-src/runtime/spu",
    ".vendor/ps3recomp-src/runtime/memory",
    ".vendor/ps3recomp-src/runtime/syscalls",
    ".vendor/ps3recomp-src/runtime/platform",
    ".vendor/ps3recomp-src/libs/video",
    "src/port",
]

# The runtime library is prebuilt and carries defaultlib directives that do not
# pull the UCRT import libraries when link.exe is driven directly (rather than
# through the clang-cl driver), leaving _aligned_malloc, sinf and friends
# unresolved. Name them explicitly, and silence the msvcrt/ucrt conflict the
# prebuilt objects otherwise report.
# link.exe is driven directly, so the CRT import libraries the clang-cl driver
# would normally add must be named here. Objects are built /MD, matching the
# prebuilt runtime, so these are the import (not static) variants.
#: Lifted SPU images and their registry, produced by
#: tools/build_spu_workloads.py. Optional: a tree without them still builds,
#: but any guest SPU job is dropped at runtime.
SPU_DIR = ROOT / "generated/spuimg"

SYSTEM_LIBS = [
    "ole32.lib", "dbghelp.lib", "user32.lib", "gdi32.lib", "winmm.lib",
]


def find_vs() -> Path:
    vswhere = Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / \
        "Microsoft Visual Studio/Installer/vswhere.exe"
    if not vswhere.is_file():
        raise SystemExit(f"vswhere not found at {vswhere}; install VS Build Tools 2022")
    out = subprocess.run(
        [str(vswhere), "-latest", "-products", "*",
         "-requires", "Microsoft.VisualStudio.Component.VC.Tools.x86.x64",
         "-property", "installationPath"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    if not out:
        raise SystemExit("no Visual Studio installation with the C++ toolset was found")
    return Path(out)


def find_msvc(vs: Path) -> Path:
    tools = vs / "VC/Tools/MSVC"
    versions = sorted((p for p in tools.iterdir() if p.is_dir()), key=lambda p: p.name)
    if not versions:
        raise SystemExit(f"no MSVC toolset under {tools}")
    return versions[-1]


def find_sdk() -> Path:
    kits = Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Windows Kits/10"
    versions = sorted((p for p in (kits / "Include").iterdir() if p.is_dir()), key=lambda p: p.name)
    if not versions:
        raise SystemExit(f"no Windows SDK under {kits}")
    return versions[-1]


def find_clang() -> Path:
    for candidate in (ROOT / ".tools/llvm-23/bin/clang-cl.exe",
                      ROOT / ".tools/llvm/bin/clang-cl.exe"):
        if candidate.is_file():
            return candidate
    raise SystemExit("clang-cl.exe not found under .tools/; run scripts/install-tools.ps1")


def toolchain_env() -> dict[str, str]:
    vs = find_vs()
    msvc = find_msvc(vs)
    sdk_ver = find_sdk()
    sdk = Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Windows Kits/10"
    clang = find_clang()

    env = dict(os.environ)
    # Ninja ships inside the Visual Studio tree, not on PATH.
    ninja_dir = vs / "Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja"
    env["PATH"] = os.pathsep.join([
        str(clang.parent),
        str(msvc / "bin/HostX64/x64"),
        str(sdk / f"bin/{sdk_ver.name}/x64"),
        str(ninja_dir),
        env.get("PATH", ""),
    ])
    env["INCLUDE"] = os.pathsep.join([
        str(msvc / "include"),
        str(sdk / f"Include/{sdk_ver.name}/ucrt"),
        str(sdk / f"Include/{sdk_ver.name}/um"),
        str(sdk / f"Include/{sdk_ver.name}/shared"),
    ])
    env["LIB"] = os.pathsep.join([
        str(msvc / "lib/x64"),
        str(sdk / f"Lib/{sdk_ver.name}/ucrt/x64"),
        str(sdk / f"Lib/{sdk_ver.name}/um/x64"),
    ])
    return env


def spu_sources() -> list[Path]:
    """Lifted SPU images plus their registry and the dispatch shim."""
    if not SPU_DIR.is_dir():
        return []
    sources = sorted(SPU_DIR.glob("*/spu_recomp.c"))
    registry = SPU_DIR / "registry"
    if registry.is_file():
        sources.append(registry)
    if sources:
        sources.append(ROOT / ".vendor/ps3recomp-src/runtime/spu/spu_dispatch_mt.c")
    return sources


def generated_sources() -> list[Path]:
    sources = sorted((ROOT / "generated").glob("*.cpp"))
    if not sources:
        raise SystemExit("no generated sources; run the lifter first")
    return sources


def ninja_escape(text: str) -> str:
    return text.replace("$", "$$").replace(" ", "$ ")


def write_build_ninja(clang: Path, optimize_generated: bool = True) -> Path:
    sources: list[tuple[Path, str]] = []
    for path in generated_sources():
        sources.append((path, "gen"))
    for rel in PORT + SCAFFOLD:
        sources.append((ROOT / rel, "scaffold"))

    includes = " ".join(f'/I"{ninja_escape(str(ROOT / d))}"' for d in INCLUDE_DIRS)

    # Generated code: warnings off, no FP contraction, and the wrap-on-overflow
    # semantics the lift assumes.
    #
    # The optimisation level is a deliberate knob. -O1 on a 600k-line TU costs
    # ~10 minutes and ~2.5 GB; on a 4-core/8 GB host that pages out and the
    # build crawls. /Od trades runtime speed for a build that finishes, which is
    # the right trade for a first boot. Rebuild with --optimize once the title
    # runs.
    opt = "/O1" if optimize_generated else "/Od"
    gen_flags = (f"/nologo /c /std:c++20 /bigobj /MD {opt} /w -fwrapv "
                 f"-fno-strict-aliasing -ffp-contract=off "
                 f"/D_CRT_SECURE_NO_WARNINGS {includes}")
    scaffold_flags = (f"/nologo /c /std:c++20 /bigobj /MD /O2 /W3 "
                      f"/D_CRT_SECURE_NO_WARNINGS {includes}")

    lines = [
        "# Generated by scripts/build.py -- do not edit.",
        "ninja_required_version = 1.11",
        f"clang = {ninja_escape(str(clang))}",
        "",
        "rule gen",
        f"  command = {ninja_escape(str(clang))} {gen_flags} /Fo$out $in",
        "  description = CC $out",
        "",
        "rule scaffold",
        f"  command = {ninja_escape(str(clang))} {scaffold_flags} /Fo$out $in",
        "  description = CC $out",
        "",
        "rule spu",
        # The SPU images are small and decode-hot, so they get full
        # optimisation even when the PPU TUs are built /Od. -x c because the
        # registry file carries no extension.
        "  command = " + ninja_escape(str(clang)) +
        f" /nologo /c -x c /MD /O2 /w /DSPU_USE_DISPATCH_MT /I\"{ninja_escape(str(ROOT / '.vendor/ps3recomp-src/runtime/spu'))}\" /Fo$out $in",
        "  description = SPUCC $out",
        "",
        "rule link",
        # clang-cl is the link driver, not link.exe directly: the driver adds
        # the CRT import libraries, the compiler-support objects (__chkstk,
        # __security_cookie, _fltused, TLS index) and the Win32 default
        # libraries that a bare link.exe invocation does not, which is what left
        # ~100 symbols unresolved when link.exe was called by hand.
        "  command = " + ninja_escape(str(clang)) + " /nologo /MD /Fe:$out $in " +
        " ".join(SYSTEM_LIBS) + ' "' +
        ninja_escape(str(ROOT / ".vendor/ps3recomp-v0.19.0-win-x64/lib/ps3recomp_runtime.lib")) +
        '"',
        "  description = LINK $out",
        "",
    ]

    # Ninja edges cannot carry a drive letter (the colon is a separator), so
    # every edge path is written relative to the build directory with forward
    # slashes. Absolute paths are only used inside rule commands, where a colon
    # is harmless.
    def rel(p: Path) -> str:
        return os.path.relpath(p, BUILD).replace("\\", "/")

    objs = []
    for path, kind in sources:
        obj = OBJ / (path.stem + ".obj")
        objs.append(obj)
        rule = "gen" if kind == "gen" else "scaffold"
        lines.append(f"build {rel(obj)}: {rule} {rel(path)}")

    for index, path in enumerate(spu_sources()):
        # Every image is named spu_recomp.c, and the registry has no extension
        # at all, so object names are derived from the parent directory.
        stem = path.parent.name if path.name == "spu_recomp.c" else path.name
        obj = OBJ / f"spu_{index:02d}_{stem[:16]}.obj"
        objs.append(obj)
        lines.append(f"build {rel(obj)}: spu {rel(path)}")
    lines.append("")
    lines.append("build SkyClimax.exe: link " + " ".join(rel(o) for o in objs))
    lines.append("")
    lines.append("default SkyClimax.exe")
    lines.append("")

    BUILD.mkdir(parents=True, exist_ok=True)
    OBJ.mkdir(parents=True, exist_ok=True)
    build_file = BUILD / "build.ninja"
    build_file.write_text("\n".join(lines), encoding="utf-8")
    return build_file


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build SkyClimax with clang-cl + Ninja.")
    parser.add_argument("--configure-only", action="store_true",
                        help="write build.ninja and stop")
    parser.add_argument("--jobs", type=int, default=os.cpu_count() or 4,
                        help="parallel compile jobs (default: logical CPUs)")
    parser.add_argument("--optimize", action="store_true",
                        help="compile the generated TUs at -O1 (slow build, fast runtime); "
                             "default is -Od for a first boot")
    args = parser.parse_args(argv)

    env = toolchain_env()
    clang = find_clang()
    ninja = shutil.which("ninja", path=env["PATH"])
    if not ninja:
        raise SystemExit("ninja not found; it ships with VS Build Tools")

    build_file = write_build_ninja(clang, optimize_generated=args.optimize)
    count = len(list((ROOT / "generated").glob("*.cpp"))) + len(PORT) + len(SCAFFOLD)
    print(f"build.ninja written: {count} translation units")
    print(f"clang-cl: {clang}")
    print(f"ninja:    {ninja}")

    if args.configure_only:
        return 0

    print(f"building with {args.jobs} jobs (the generated TUs are large)")
    result = subprocess.run([ninja, "-C", str(BUILD), f"-j{args.jobs}"], env=env)
    if result.returncode != 0:
        print(f"build failed with exit code {result.returncode}", file=sys.stderr)
        return result.returncode

    exe = BUILD / "SkyClimax.exe"
    if not exe.is_file():
        print("ninja reported success but SkyClimax.exe is missing", file=sys.stderr)
        return 1
    print(f"built {exe} ({exe.stat().st_size / 1e6:.1f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
