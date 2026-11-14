# Compilação

Estado: **a compilação nativa nunca foi executada neste hospedeiro.** Não há
compilador C/C++, CMake ou Ninja instalados. Tudo abaixo é o procedimento a
executar quando esse pré-requisito existir; está marcado como planejado, não
validado.

## Pré-requisitos

| Componente | Versão | Motivo |
|---|---|---|
| Visual Studio Build Tools 2022 | 17.x, "Desktop development with C++" | o MSVC fornece `cl`; o código gerado usa `__declspec(thread)` |
| CMake | ≥ 3.20 | geração da build |
| Ninja | ≥ 1.11 | builds incrementais rápidas |
| Windows SDK | 10.0.22621 ou mais recente | cabeçalhos de D3D12 |

`clang-cl` é um substituto aceitável para `cl` se a STL do MSVC estiver
disponível.

## Etapa 1 — extrair o pacote

```bash
python .vendor/ps3recomp/tools/pkg_extract.py "$SKYCLIMAX_PKG" work/pkg
```

Validado: 46 arquivos, 551 MB, sem erros.

## Etapa 2 — obter um executável descriptografado

Bloqueado. Veja [problemas conhecidos](../troubleshooting/known-issues.md). O
artefato esperado é `work/game/EBOOT.elf`, uma imagem `ET_EXEC` PPC64
big-endian.

## Etapa 3 — carregar

```bash
python .vendor/ps3recomp/tools/ppu_loader.py work/game/EBOOT.elf -o work/meta
```

Produz `EBOOT.functions.json`, `.image.json`, `.loader.json`, `.imports.json`.
A lista de importações é o que diz quais módulos HLE precisam existir; em uma
imagem descriptografada, espere contagens na casa das centenas de NIDs, como os
projetos de referência relatam para títulos comparáveis.

## Etapa 4 — elevar

```bash
python .vendor/ps3recomp/tools/ppu_lifter.py work/game/EBOOT.elf \
  -o generated/ \
  --functions work/meta/EBOOT.functions.json \
  --imports  work/meta/EBOOT.imports.json
```

Validado em um ELF sintético: 1 função produziu `ppu_recomp_000.cpp`
(1.117 linhas) mais `ppu_recomp.h`.

## Etapa 5 — stubs

```bash
python .vendor/ps3recomp/tools/generate_stubs.py work/meta/EBOOT.imports.json -o src/hle
```

Ainda não executado contra importações reais, porque a tabela de importações
está criptografada.

## Etapa 6 — configurar e compilar

```bash
cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=RelWithDebInfo
cmake --build build
```

Não executado. A primeira falha esperada em uma imagem real é um símbolo HLE
ausente, que é a forma normal de esta etapa anunciar qual módulo falta
implementar em seguida.

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
