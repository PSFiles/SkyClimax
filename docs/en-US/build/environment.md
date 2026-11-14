# Environment setup

Target: Windows 10/11 x64, Git Bash or PowerShell, no administrator rights
required for anything below (everything installs inside the repository).

## 1. Directory layout

| Path | Contents | In git |
|---|---|---|
| `.tools/` | JDK, Node, Ghidra, npm packages | no |
| `.vendor/` | ps3recomp release | no |
| `.venv/` | Python virtual environment | no |
| `work/` | extracted package, reports, build tree | no |

`scripts/install-tools.ps1` creates all four.

## 2. Python environment

```bash
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e ".[dev]"
```

Verified on this machine:

```text
Python 3.13.14
capstone 5.0.7
pyelftools 0.33
pycryptodome 4.4.0
```

## 3. JDK 25 for Ghidra

Ghidra 12.2 refuses to start on JDK 21. The required version is declared in
`Ghidra/application.properties`:

```text
application.java.min=25
application.java.compiler=25
```

Install Temurin 25 and export it:

```bash
export JAVA_HOME="$(pwd)/.tools/jdk25/jdk-25.0.5+8"
"$JAVA_HOME/bin/java" -version
```

Expected:

```text
openjdk version "25.0.5" 2026-10-20 LTS
```

## 4. Ghidra

```bash
.tools/ghidra/ghidra_12.2_PUBLIC/support/analyzeHeadless
```

With `JAVA_HOME` set, this prints the headless usage banner. Without it, it
prints `WARNING: JAVA_HOME environment specifies unsupported java version`.

## 5. Node.js and REA

REA 6.9.0 requires `node ^22.23.4 || ^24.22.1 || >=26.12.1`. The Node bundled
with this workstation (22.22.2) is outside that range, so Node 24.22.3 is
installed under `.tools/`:

```bash
export PATH="$(pwd)/.tools/node/node-v24.22.3-win-x64:$PATH"
node --version
```

Expected:

```text
v24.22.3
```

REA is installed into `.tools/rea` and launched through its entry script,
because npm does not create a `.bin` shim when `--prefix` is used without a
`package.json`:

```bash
node .tools/rea/node_modules/rea-agents/scripts/rea.mjs --version
```

Expected:

```text
6.9.0
```

Set `GHIDRA_INSTALL_DIR` before calling `rea capabilities`, otherwise the Ghidra
provider reports `GHIDRA_INSTALL_DIR is not set`:

```bash
export GHIDRA_INSTALL_DIR="$(pwd)/.tools/ghidra/ghidra_12.2_PUBLIC"
```

## 6. ps3recomp

```bash
unzip -q ps3recomp-v0.19.0-win-x64.zip -d .vendor/
.venv/Scripts/python.exe -m pip install -r .vendor/ps3recomp-v0.19.0-win-x64/tools/requirements.txt
```

Confirm the pinned build:

```bash
cat .vendor/ps3recomp-v0.19.0-win-x64/VERSION.txt
```

```text
ps3recomp v0.19.0
platform: win-x64
commit:   ae92407bb1d899e3d32143e360fe6e6d4d8fa1b5
```

## 7. Environment variables

| Variable | Purpose |
|---|---|
| `JAVA_HOME` | must point at JDK 25 for Ghidra |
| `GHIDRA_INSTALL_DIR` | REA's Ghidra provider |
| `SKYCLIMAX_PKG` | path to the retail package (defaults to the repository root) |
| `SKYCLIMAX_EXTRACTED` | extracted tree (defaults to `work/pkg`) |

`scripts/versions.env` holds the pinned versions and is the single source of
truth for the installers.

## 8. Verification

```bash
.venv/Scripts/python.exe -m pytest
.venv/Scripts/python.exe scripts/check_docs_parity.py
```

Both must pass before any work is considered finished.
