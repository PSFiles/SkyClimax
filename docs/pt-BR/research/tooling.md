# Ferramentas

Cada versão abaixo foi instalada de uma fonte oficial e exercitada nesta
máquina. O que não pôde ser instalado está listado em
[problemas conhecidos](../troubleshooting/known-issues.md), em vez de ser
declarado disponível.

## Versões fixadas

| Ferramenta | Versão | Fonte | Comando de verificação | Resultado |
|---|---|---|---|---|
| Ghidra | 12.2 (build 2026-10-16) | release do GitHub `Ghidra_12.2_build` | `support/analyzeHeadless` | banner de uso impresso, saída 1 |
| Temurin JDK | 25.0.5+8 | API do Adoptium, `latest/25/ga` | `bin/java -version` | `openjdk version "25.0.5"` |
| Node.js | 24.22.3 | nodejs.org `dist/v24.22.3` | `node --version` | `v24.22.3` |
| Python | 3.13.14 (venv) | interpretador local | `python -V` | `Python 3.13.14` |
| capstone | 5.0.7 | PyPI | `capstone.__version__` | `5.0.7` |
| pyelftools | 0.33 | PyPI | `elftools.__version__` | `0.33` |
| pycryptodome | 4.4.0 | PyPI | `Crypto.__version__` | `4.4.0` |
| LIEF | 1.0.0 | PyPI | `lief.__version__` | `1.0.0-d05b3499b` |
| ps3recomp | 0.19.0 | arquivo fornecido | `VERSION.txt` | `commit ae92407b…`, `win-x64` |

## O Ghidra exige JDK 25, não JDK 21

O Ghidra 12.2 declara `application.java.min=25` em
`Ghidra/application.properties`. Apontar `JAVA_HOME` para uma instalação de
JDK 21 falha com:

```text
WARNING: JAVA_HOME environment specifies unsupported java version
ERROR: Unable to prompt user for JDK path, no TTY detected.
```

Por isso o projeto fixa o JDK 25 e exporta `JAVA_HOME` explicitamente antes de
cada invocação do Ghidra.

## REA

O REA é distribuído como o pacote npm `rea-agents`. A versão 6.9.0 declara:

```json
{ "node": "^22.23.4 || ^24.22.1 || >=26.12.1" }
```

O Node.js empacotado com a estação de trabalho é 22.22.2, que **não** satisfaz
essa faixa; por isso o Node 24.22.3 é instalado dentro de `.tools/` e
prepended ao `PATH` apenas para o REA. Veja
[problemas conhecidos](../troubleshooting/known-issues.md) para o estado da
instalação nesta sessão.

## ps3recomp

O `ps3recomp` v0.19.0 é o backend de recompilação. Ele não é vendorizado no git
porque é uma release binária; `scripts/install-tools.ps1` o baixa para
`.vendor/`. O `VERSION.txt` dele reporta:

```text
ps3recomp v0.19.0
platform: win-x64
commit:   ae92407bb1d899e3d32143e360fe6e6d4d8fa1b5
status:   renders and runs recompiled titles (D3D12)
```

As ferramentas usadas pelo SkyClimax são `pkg_extract.py`, `ppu_loader.py`,
`ppu_lifter.py`, `ppu_disasm.py`, `generate_stubs.py`, `ghidra_analyze.py` e
`unfself.py`.

## Lacuna da toolchain Windows

`cl`, `cmake`, `ninja`, `gcc` e `clang` estão todos ausentes desta máquina,
portanto nenhum executável nativo pode ser produzido aqui. O C++ gerado é,
portanto, verificado estruturalmente e por inspeção, nunca por compilação.
Instalar o Visual Studio Build Tools é o único pré-requisito que desbloqueia o
próximo marco; veja [compilação](../build/build.md).
