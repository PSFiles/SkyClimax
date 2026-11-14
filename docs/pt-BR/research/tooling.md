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
| VS Build Tools | 17.14.45 (MSVC 14.44.35207) | instalação manual | `vswhere -latest` | `C://Program Files (x86)\Microsoft Visual Studio\2022\BuildTools` |
| Windows SDK | 10.0.26100.0 | vem com o Build Tools | listagem de diretório | `10.0.26100.0` |
| LLVM / clang-cl | 23.1.5 | release do GitHub `llvmorg-23.1.5` | `clang-cl --version` | `clang version 23.1.5` |
| Ninja | vem com o Build Tools | — | `ninja --version` | usado via `scripts/build.py` |

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
adicionado ao início do `PATH` apenas para o REA. Veja
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

## Por que clang-cl e não cl.exe

O `ppu_recomp.h` gerado usa `__atomic_load_n`, `__atomic_store_n`,
`__builtin_bswap32/64` e `__builtin_expect` incondicionalmente. O `cl.exe` não
tem equivalente, e o cabeçalho é gerado por máquina, então não pode ser
corrigido à mão. A própria CI do kit faz a verificação de compilação do caminho
Windows com clang-cl, que é portanto o compilador suportado aqui. O MSVC ainda
fornece os cabeçalhos, as bibliotecas e o `link.exe`; o clang-cl é apenas o
front end.

## Por que o CMake não é usado

A sondagem de compilador do CMake invoca `reg.exe` para consultar a instalação
do Visual Studio. Esse programa é bloqueado pela lista negra deste ambiente, e o
bloqueio não pode ser aprovado a partir de um comando. Em vez de contornar um
controle de segurança, a compilação é conduzida por `scripts/build.py`, que
localiza a toolchain, emite `build/build.ninja` para as 24 unidades de tradução
e executa o Ninja. `src/port/CMakeLists.txt` é mantido para hospedeiros onde o
CMake é utilizável.

Veja [compilação](../build/build.md) para o procedimento.
