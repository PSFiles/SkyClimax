# Compilação

Estado: **a compilação nativa nunca foi executada neste hospedeiro.** Não há
compilador C/C++, CMake ou Ninja instalados. As etapas 1–4 estão validadas; as
etapas 5–7 estão planejadas.

## Pré-requisitos

| Componente | Versão | Motivo |
|---|---|---|
| Visual Studio Build Tools 2022 | 17.x, "Desktop development with C++" | o MSVC fornece `cl`; o código gerado usa `__declspec(thread)` |
| CMake | ≥ 3.20 | geração da build |
| Ninja | ≥ 1.11 | builds incrementais rápidas |
| Windows SDK | 10.0.22621 ou mais recente | cabeçalhos de D3D12 |
| Fontes do runtime do ps3recomp | v0.19.0 | `ppu_load_elf`, `ppu_recomp_register`, `ppu_hle_init`, `ppu_run` |

`clang-cl` é um substituto aceitável para `cl` se a STL do MSVC estiver
disponível.

A release binária traz cabeçalhos e `lib/ps3recomp_runtime.lib`, mas **não** as
fontes do runtime. O template de projeto do upstream as linka a partir de um
checkout indicado por `PS3RECOMP_DIR`, então a build também precisa desse
checkout. Isso está registrado como KI-009.

## Etapa 1 — extrair o pacote

```bash
python .vendor/ps3recomp/tools/pkg_extract.py "$SKYCLIMAX_PKG" work/pkg
```

Validado: 46 arquivos, 551 MB, sem erros.

## Etapa 2 — obter um executável descriptografado

Validado. O dono forneceu `EBOOT.elf` (5.653.432 bytes, SHA-256
`d3a13dd3…d6d33b777`). Ele só foi aceito depois de coincidir com a declaração do
contêiner criptografado: `e_machine = 21`, `e_entry = 0x4CDF00`, 8 cabeçalhos de
programa, 31 cabeçalhos de seção.

## Etapa 3 — carregar

```bash
python .vendor/ps3recomp/tools/ppu_loader.py work/game/EBOOT.elf -o work/meta
```

Validado:

```text
entry (OPD)      : 0x4cdf00 -> code 0x10230, toc 0x4ed088
OPD descriptors  : 11827
unique functions : 11338
firmware imports : 207 across 14 libraries
```

Produz `EBOOT.functions.json`, `.image.json`, `.loader.json`, `.imports.json`.

## Etapa 4 — elevar

```bash
python .vendor/ps3recomp/tools/ppu_lifter.py work/game/EBOOT.elf \
  -o generated/ \
  --functions work/meta/EBOOT.functions.json \
  --hle-stubs work/meta/EBOOT.imports.json
```

Validado: 15.237 funções, 17 blocos, 9.571.078 linhas, 9m10s, 2 avisos — ambos
`has no continuation at 0x004B7060`, que é o fim do segmento de texto e,
portanto, um artefato de fronteira, não uma função mal dimensionada.

Atenção ao nome da opção: é `--hle-stubs`, não `--imports`. A documentação do
próprio liftedor em `docs/PPU_RECOMP.md` diz `--imports`, mas a CLI distribuída
não a aceita. O arquivo de `--hle-stubs` é o mesmo `imports.json`.

## Etapa 5 — geração de stubs

Não é necessária para este título. O runtime já implementa todas as 14
bibliotecas importadas; `generate_stubs.py` existe para bibliotecas ausentes.
Mantenha-o como recurso para quando um NID se revelar não implementado em
execução.

## Etapa 6 — configurar e compilar

```bash
cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=RelWithDebInfo \
      -DPS3RECOMP_DIR=/path/to/ps3recomp
cmake --build build
```

Não executado. Espere dois problemas primeiro: as fontes do runtime precisam
estar presentes, e 9,57 M linhas de C++ gerado podem exigir `/bigobj` e mais
divisão em blocos.

## Etapa 7 — executar

```bash
./build/skyclimax.exe --log-level info
```

Não executado.

## O que "concluído" significa por etapa

| Etapa | Evidência exigida |
|---|---|
| extrair | 46 arquivos, tamanhos em bytes iguais à listagem do extrator |
| descriptografar | SHA-256 do ELF registrado em `work/reports/` |
| carregar | contagem de funções diferente de zero, lista de importações não vazia |
| elevar | arquivos gerados compilam *e* a contagem de funções bate com a do carregador |
| stub | cada NID importado resolve para um símbolo do hospedeiro |
| compilar | `skyclimax.exe` existe e `--version` executa |
| executar | um quadro é apresentado, capturado e anexado a um relatório |

Uma etapa nunca é marcada como concluída só porque a anterior deu certo.
