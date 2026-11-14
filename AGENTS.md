# AGENTS.md

Instructions for any agent or contributor working in this repository. Read this
file completely before changing anything.

Português do Brasil: [AGENTS.pt-BR.md](AGENTS.pt-BR.md) — same content, same
structure. Both files change together.

## 1. What this project is

SkyClimax statically recompiles **After Burner Climax** (PS3, `NPUB30151`) to
native Windows x64. It is **experimental** and currently blocked on decrypting
the retail executable. Do not describe it as working, playable or complete.

The backend is [ps3recomp](https://github.com/sp00nznet/ps3recomp) v0.19.0,
vendored into `.vendor/` (not committed). SkyClimax adds analysis tooling and,
later, game-specific compatibility code.

## 2. Architecture you must respect

```text
.pkg ──pkg_extract.py──▶ EBOOT.BIN ──[KEY REQUIRED]──▶ EBOOT.elf
      ──ppu_loader.py──▶ functions/image/imports JSON
      ──ppu_lifter.py──▶ ppu_recomp_*.cpp ──MSVC──▶ skyclimax.exe + ps3recomp runtime
```

Layer ownership:

| Layer | Owner | Rule |
|---|---|---|
| Container readers | SkyClimax (`src/skyclimax/`) | pure Python, no third-party runtime deps |
| Recompiler and runtime | ps3recomp (vendored) | never edit in place; patch under `tools/patches/` |
| Game-specific compatibility | SkyClimax (`src/hle/`) | only added when a real import demands it |
| Build and CI | SkyClimax | CMake + scripts |

Never hand-edit generated C++. It is regenerated on every lift.

## 3. Pinned tools

Versions live in `scripts/versions.env` and are recorded in
`docs/en-US/research/tooling.md`. Do not upgrade a tool without updating both
files and re-recording the verification output.

| Tool | Version | Note |
|---|---|---|
| Ghidra | 12.2 | requires JDK 25 (`application.java.min=25`) |
| Temurin JDK | 25.0.5+8 | JDK 21 is rejected |
| Node.js | 24.22.3 | REA 6.9.0 needs `^22.23.4 \|\| ^24.22.1 \|\| >=26.12.1` |
| Python | 3.13.x | venv in `.venv/` |
| ps3recomp | 0.19.0 | commit `ae92407bb1d899e3d32143e360fe6e6d4d8fa1b5` |

## 4. Hard rules

1. **Never invent data.** No function names, addresses, NIDs, structures or
   behaviour that was not observed in a file or produced by a tool. If a value
   is unknown, write that it is unknown and say what would determine it.
2. **Never fake a stub.** A stub that returns success without implementing
   behaviour must be named `stub_<nid>_unimplemented` and log once on first call.
   It must appear in the compatibility matrix as unimplemented.
3. **Never claim a test passed without running it.** Paste the command and its
   real output in the commit message or the report.
4. **Never mark a milestone validated without evidence.** Evidence means a
   command plus its recorded result in `docs/*/compatibility-matrix.md`.
5. **Never commit game data.** No `.pkg`, `.rap`, `.elf`, `.self`, decrypted
   assets, keys or `work/` contents. `.gitignore` already covers these.
6. **Never modify original game files.** All extraction goes to `work/`.
7. **Never bypass a documented blocker silently.** If you cannot decrypt,
   compile or run something, say so and update the known-issues document.

## 5. Bilingual documentation rule

- `docs/en-US/` is the source language; `docs/pt-BR/` is a faithful translation.
  Same files, same heading structure, same code blocks.
- Prose is translated. Code, commands, paths, identifiers, log messages and
  low-level diagnostics stay in English.
- Every document that changes must change in both trees **in the same commit**.
- Run the gate before finishing:

```bash
python scripts/check_docs_parity.py
```

- If a translation is incomplete, add `TODO(pt-BR)` and list it in
  `docs/README.md`. Never mark a partial translation as done.
- Terminology comes from `docs/en-US/glossary.md`. Do not invent synonyms.

## 6. Code conventions

- Python: 3.10+, `from __future__ import annotations`, type hints on public
  functions, dataclasses for records, no third-party imports in `src/skyclimax/`.
- Every parser module documents its byte layout in the module docstring and
  names the real file that verified it.
- Parsers raise on malformed input; they never truncate silently or guess.
- CLI: `argparse`, subcommand per format, `--json` for machine output, errors to
  stderr with exit code 1.
- C/C++ (generated and HLE): C++20, `extern "C"` at the boundary, guest memory
  only through `vm_read*`/`vm_write*`.
- Comments explain *why*, not *what*. Never comment out code; delete it.

## 7. Analysis rules

1. Establish the container format from the file itself (magic, sizes, entropy),
   not from its extension.
2. Cross-validate counts: a header field that claims N items must be checked
   against the number of items actually parsed.
3. When a layout probe fails, report the failure and stop. Do not try variants
   until something "looks plausible".
4. Record every non-obvious number in the docs with the command that produced it.
5. Prefer `work/reports/*.json` as the evidence trail; those files are ignored by
   git but reproducible.

## 8. Build and test

```bash
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e ".[dev]"
.venv/Scripts/python.exe -m pytest
.venv/Scripts/python.exe scripts/check_docs_parity.py
```

- Unit tests must pass on a clean checkout with no game files present.
- Integration tests are skipped automatically when the package is absent; never
  make the suite depend on the game.
- CI runs both gates on Windows. A red CI blocks merge.

## 9. Working method

- Work in small, verifiable steps with an objective completion criterion.
- Before changing a parser, save its current output and diff after the change.
- Before claiming a construct is unsupported, check the backend documentation
  and the tool's `--help`.
- Update `docs/*/compatibility-matrix.md` whenever a capability changes state.
- Record new architectural decisions as an ADR in
  `docs/en-US/architecture/decisions.md` and its pt-BR twin; append, never rewrite.

## 10. Definition of done

A task is done when all of the following hold:

1. The code or documentation change is complete and consistent.
2. `pytest` passes locally with its output recorded.
3. `check_docs_parity.py` passes.
4. Both language trees are updated.
5. The compatibility matrix reflects the new state.
6. The commit message states what changed and which command verified it.

A task is **not** done because it compiles, because the code "looks right", or
because a previous step succeeded.
