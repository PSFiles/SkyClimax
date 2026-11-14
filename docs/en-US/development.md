# Development guide

## Set up

Follow [environment setup](build/environment.md). Then:

```bash
.venv/Scripts/python.exe -m pytest
.venv/Scripts/python.exe scripts/check_docs_parity.py
```

## Layout

```text
src/skyclimax/       analysis library (no third-party runtime dependencies)
tests/               pytest suite; synthetic fixtures + optional real-package tests
scripts/             installers, parity checker, verification helpers
docs/en-US/          source-of-truth documentation
docs/pt-BR/          faithful translation, machine-checked
generated/           lifter output (git-ignored)
```

## Changing a parser

1. Reproduce the current behaviour against the real file and save the JSON
   report under `work/reports/`.
2. Change the parser.
3. Re-run the same command and diff the two reports.
4. Add or update a synthetic fixture test in `tests/conftest.py` so the change
   is covered without the retail package.
5. Update the module docstring — it is the format specification.
6. Update both language trees and run the parity checker.

Never change a parser to make a fixture pass. If the fixture disagrees with the
real file, the fixture is wrong.

## Adding a new container format

1. Add `src/skyclimax/<format>.py` with a module docstring containing the byte
   layout and a note on which real file verified it.
2. Add a `build_<format>()` helper to `tests/conftest.py`.
3. Add tests for the happy path, a truncated file, and a wrong magic.
4. Register the magic in `MAGIC_PROBES` so `inventory` classifies it.
5. Add a CLI subcommand that prints JSON and supports `--json`.
6. Document it in `docs/en-US/analysis/assets.md` **and** the pt-BR twin.

## Adding HLE coverage

Only when a real import demands it:

1. Capture the failing call: NID, library, caller address, arguments.
2. Find the documented behaviour of that export.
3. Implement it in `src/hle/`, returning the documented error codes.
4. Add a test that calls it with the same arguments and asserts the return.
5. Record the NID in the compatibility matrix.

A stub that returns success without implementing behaviour is not coverage. If a
function must be stubbed, name it `stub_<nid>_unimplemented` and log once at
first call.

## Reproducing a defect

Record four things: the command, the input, the expected result and the observed
result. If a crash is involved, capture the guest address and the host stack
separately — a guest fault and a host fault have completely different causes.

## Tests

| Kind | Location | Requires the game |
|---|---|---|
| Unit | `tests/test_containers.py` | no |
| Integration | `tests/test_real_package.py` | yes, auto-skipped |
| Docs parity | `scripts/check_docs_parity.py` | no |

CI runs the unit tests and the parity checker on Windows. Integration tests are
skipped there because the package is not in the repository.

## Commit rules

- One coherent change per commit.
- Documentation and its translation land in the same commit.
- A commit that changes behaviour states the command used to verify it.
- Never commit `work/`, `.tools/`, `.vendor/`, `.venv/` or any game file.

## Adding a milestone

Milestones live in [architecture overview](architecture/overview.md). A milestone
moves to `validated` only when a command and its output are recorded in the
compatibility matrix's validation log.
