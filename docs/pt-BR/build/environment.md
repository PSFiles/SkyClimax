# Preparação do ambiente

Alvo: Windows 10/11 x64, Git Bash ou PowerShell, sem necessidade de direitos de
administrador para nada abaixo (tudo é instalado dentro do repositório).

## 1. Layout de diretórios

| Caminho | Conteúdo | No git |
|---|---|---|
| `.tools/` | JDK, Node, Ghidra, pacotes npm | não |
| `.vendor/` | release do ps3recomp | não |
| `.venv/` | ambiente virtual Python | não |
| `work/` | pacote extraído, relatórios, árvore de compilação | não |

`scripts/install-tools.ps1` cria os quatro.

## 2. Ambiente Python

```bash
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e ".[dev]"
```

Verificado nesta máquina:

```text
Python 3.13.14
capstone 5.0.7
pyelftools 0.33
pycryptodome 4.4.0
```

## 3. JDK 25 para o Ghidra

O Ghidra 12.2 se recusa a iniciar com JDK 21. A versão exigida está declarada em
`Ghidra/application.properties`:

```text
application.java.min=25
application.java.compiler=25
```

Instale o Temurin 25 e exporte-o:

```bash
export JAVA_HOME="$(pwd)/.tools/jdk25/jdk-25.0.5+8"
"$JAVA_HOME/bin/java" -version
```

Esperado:

```text
openjdk version "25.0.5" 2026-10-20 LTS
```

## 4. Ghidra

```bash
.tools/ghidra/ghidra_12.2_PUBLIC/support/analyzeHeadless
```

Com `JAVA_HOME` definido, isso imprime o banner de uso do headless. Sem ele,
imprime `WARNING: JAVA_HOME environment specifies unsupported java version`.

## 5. Node.js e REA

O REA 6.9.0 exige `node ^22.23.4 || ^24.22.1 || >=26.12.1`. O Node empacotado
com esta estação de trabalho (22.22.2) está fora dessa faixa, então o Node
24.22.3 é instalado em `.tools/`:

```bash
export PATH="$(pwd)/.tools/node/node-v24.22.3-win-x64:$PATH"
node --version
```

Esperado:

```text
v24.22.3
```

O REA é instalado em `.tools/rea` e iniciado pelo seu script de entrada, porque
o npm não cria um atalho em `.bin` quando `--prefix` é usado sem um
`package.json`:

```bash
node .tools/rea/node_modules/rea-agents/scripts/rea.mjs --version
```

Esperado:

```text
6.9.0
```

Defina `GHIDRA_INSTALL_DIR` antes de chamar `rea capabilities`, caso contrário o
provedor Ghidra reporta `GHIDRA_INSTALL_DIR is not set`:

```bash
export GHIDRA_INSTALL_DIR="$(pwd)/.tools/ghidra/ghidra_12.2_PUBLIC"
```

## 6. ps3recomp

```bash
unzip -q ps3recomp-v0.19.0-win-x64.zip -d .vendor/
.venv/Scripts/python.exe -m pip install -r .vendor/ps3recomp-v0.19.0-win-x64/tools/requirements.txt
```

Confirme a build fixada:

```bash
cat .vendor/ps3recomp-v0.19.0-win-x64/VERSION.txt
```

```text
ps3recomp v0.19.0
platform: win-x64
commit:   ae92407bb1d899e3d32143e360fe6e6d4d8fa1b5
```

## 7. Variáveis de ambiente

| Variável | Finalidade |
|---|---|
| `JAVA_HOME` | precisa apontar para o JDK 25, para o Ghidra |
| `GHIDRA_INSTALL_DIR` | provedor Ghidra do REA |
| `SKYCLIMAX_PKG` | caminho do pacote de varejo (padrão: a raiz do repositório) |
| `SKYCLIMAX_EXTRACTED` | árvore extraída (padrão: `work/pkg`) |

`scripts/versions.env` contém as versões fixadas e é a fonte única de verdade
para os instaladores.

## 8. Verificação

```bash
.venv/Scripts/python.exe -m pytest
.venv/Scripts/python.exe scripts/check_docs_parity.py
```

Ambos precisam passar antes de qualquer trabalho ser considerado concluído.
