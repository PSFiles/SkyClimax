# SkyClimax

**English (en-US):** [README.md](README.md)

Recompilação estática de **After Burner Climax** (PlayStation 3, `NPUB30151`)
para Windows x64 nativo — sem emulador no meio do caminho.

> **Estado: experimental.** O projeto não produziu um executável funcional. O
> último marco efetivamente alcançado é o **M3: o pipeline de elevação está
> provado em um ELF de PS3 sintético**. O executável de varejo é criptografado e
> não pode ser descriptografado sem uma chave fornecida pelo dono do jogo. Veja
> [problemas conhecidos](docs/pt-BR/troubleshooting/known-issues.md).

## O que é este repositório

Um projeto de engenharia reproduzível em torno do recompilador estático
[ps3recomp](https://github.com/sp00nznet/ps3recomp), mais as ferramentas de
análise de que este título específico precisa:

| Componente | Estado |
|---|---|
| `src/skyclimax/` — leitores de PKG, SELF, PARAM.SFO, FArc, ADX, PSARC | implementado, testado |
| `scripts/check_docs_parity.py` — portão de documentação bilíngue | implementado, passando |
| `scripts/install-tools.*` — instalação fixada e idempotente da toolchain | implementado |
| `.github/workflows/ci.yml` — CI no Windows | implementado |
| Código recompilado do jogo | **não produzido** — bloqueado pela descriptografia |

## O que realmente se sabe sobre o jogo

Tudo abaixo foi medido no pacote de varejo, não presumido:

- Pacote `UP0177-NPUB30151_00-AFTERBURNERCMX00.pkg`, 551.772.592 bytes, 46 itens.
- `PARAM.SFO`: título `After Burner Climax`, `TITLE_ID NPUB30151`, versão `01.00`,
  firmware alvo `03.0000`.
- `EBOOT.BIN`: SELF de varejo de 5.656.176 bytes; o ELF embutido é `ET_EXEC`,
  `EM_PPC64`, big-endian, entrada `0x4CDF00` (um descritor OPD no segmento de
  dados), 8 cabeçalhos de programa. **Todos os segmentos de carga são
  criptografados com AES** (entropia 7,9973 bits/byte).
- Assets: PSARC de 407 MB (`rom.psarc`) cuja tabela de conteúdo é opaca, 101
  programas de shader Cg (`.vp`/`.fp`, gzip) em `shader_cg.farc`, 23 fluxos CRI
  ADX (31,6 minutos no total) mais um banco de vozes CRI AFS de 38,9 MB.

Detalhes e evidências: [executável](docs/pt-BR/analysis/executable.md),
[assets](docs/pt-BR/analysis/assets.md), [pacote](docs/pt-BR/analysis/package.md).

## Requisitos

| Requisito | Versão | Observação |
|---|---|---|
| Windows | 10 ou 11, x64 | desenvolvido e testado no Windows 11 23H2 |
| Python | 3.10+ | 3.13.14 usado aqui |
| Ghidra | 12.2 | exige **JDK 25** |
| Node.js | 24.22.3 | apenas para o REA; o 22.22.2 empacotado é antigo demais |
| ps3recomp | 0.19.0 | backend de recompilação |
| MSVC + CMake + Ninja | 2022 / 3.20 / 1.11 | **não instalados aqui** — necessários para o M4 |

## Instalação

```bash
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e ".[dev]"
powershell -ExecutionPolicy Bypass -File scripts/install-tools.ps1
```

## Uso

```bash
# describe the package header
python -m skyclimax pkg-info UP0177-NPUB30151_00-AFTERBURNERCMX00.pkg

# extract (needs the vendored ps3recomp tools)
python .vendor/ps3recomp/tools/pkg_extract.py UP0177-NPUB30151_00-AFTERBURNERCMX00.pkg work/pkg

# analyse the executable container
python -m skyclimax self-info work/pkg/USRDIR/EBOOT.BIN --json work/reports/self.json

# inventory every extracted file by magic
python -m skyclimax inventory work/pkg --json work/reports/inventory.json

# list or extract a Sega FArc archive
python -m skyclimax farc work/pkg/USRDIR/ps3/shader_cg.farc --extract work/shader

# verify the repository
.venv/Scripts/python.exe -m pytest
.venv/Scripts/python.exe scripts/check_docs_parity.py
```

## Marcos

| # | Marco | Estado |
|---|---|---|
| M0 | toolchain instalada e validada | validado |
| M1 | pacote aberto, inventário reproduzível | validado |
| M2 | contêiner do executável analisado | validado (apenas metadados) |
| M3 | pipeline de elevação provado em um ELF sintético | validado |
| M4 | compilação nativa do código elevado | planejado — sem compilador |
| M5 | EBOOT descriptografado elevado | planejado — sem chave |
| M6 | inicialização do runtime, primeiro quadro | planejado |
| M7 | jogável | planejado |

## Limitações conhecidas

1. **O executável é criptografado.** Nenhum nome de função, endereço ou lista de
   importações é reportado em lugar algum, porque nada disso pode ser verificado.
   Quem publicar tal lista para este título sem descriptografia está adivinhando.
2. **O `rom.psarc` está sem índice.** Sua TOC não corresponde ao layout
   documentado; 96 % da carga do pacote está atualmente ilegível.
3. **Nada foi compilado.** Não existe toolchain C/C++ no hospedeiro de
   desenvolvimento, então o C++ gerado é apenas verificado estruturalmente.
4. **O REA não consegue analisar ELF de PPU no Windows.** Seu provedor Ghidra no
   Windows aceita apenas binários PE; por isso o Ghidra é conduzido diretamente.

## Regras do repositório

- Nenhum arquivo do jogo, chave ou carga descriptografada é comitado. O
  `.gitignore` garante isso.
- A documentação existe em en-US e pt-BR e é verificada por máquina quanto à
  paridade.
- Uma funcionalidade só é `validated` quando um comando e sua saída são
  registrados.

## Documentação

Comece em [docs/README.md](docs/README.md) (índice bilíngue com estado de
paridade). Decisões de arquitetura:
[docs/pt-BR/architecture/decisions.md](docs/pt-BR/architecture/decisions.md).

## Licença

MIT para o código deste repositório. ps3recomp e Ghidra mantêm suas próprias
licenças. Nenhum material proprietário da Sega ou da Sony é distribuído aqui.
