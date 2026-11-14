# Análise de assets

Todos os números vêm do pacote extraído. Reproduza com:

```bash
python -m skyclimax inventory work/pkg --json work/reports/inventory.json
```

## Pilha de middleware

O pacote identifica seu próprio middleware pelo formato de arquivo, não por
strings em um binário que não conseguimos ler:

| Formato | Evidência | Papel |
|---|---|---|
| PSARC | magic `PSAR`, compressão `zlib`, 218 entradas de TOC | arquivo principal de assets (407 MB) |
| Sega FArc | magic `FArc` / `FArC` | arquivos de sistema e de shaders |
| CRI ADX | `0x8000` + `(c)CRI` | fluxos de música e voz |
| CRI AFS | magic `AFS\0` | contêiner de banco de vozes |
| Cg | nomes de entrada `.vp` / `.fp`, cargas gzip | programas de GPU |

## Sega FArc

Duas variantes aparecem no mesmo pacote, distinguidas pela caixa do quarto byte
de magic:

| Variante | Layout do registro | Verificada em |
|---|---|---|
| `FArc` | `cstring name, u32 offset, u32 size` | `SYSTEM.farc` (2 registros) |
| `FArC` | `cstring name, u32 offset, u32 size, u32 uncompressed_size` | `shader_cg.farc` (101 registros) |

Em ambas as variantes, o campo do cabeçalho em `0x04` é igual a
`first_data_offset - 8`, o que valeu para as duas amostras (`0x2F - 8 = 0x27`,
`0x116E - 8 = 0x1166`). Como só havia duas amostras disponíveis,
`skyclimax.farc` trata a variante como hipótese e valida cada registro contra os
limites do arquivo em vez de confiar nela.

### Arquivo de shaders

`shader_cg.farc` contém 101 registros, todos comprimidos com gzip:

| Extensão | Contagem | Interpretação |
|---|---|---|
| `.vp` | 46 | programas de vértice |
| `.fp` | 55 | programas de fragmento |

Nove nomes-base carregam todas as permutações, por exemplo
`blinn_frag_cubemap`, `blinn_frag_default`, `blinn_vert_default`,
`deck_default`, `refrac_default`, `sea_default`, `sea_nonref`, `sea_shadow`,
`sky_default`.

Duas consequências para o porte:

- Os shaders são **Cg compilado para microcódigo do PS3**, não fonte GLSL ou
  HLSL. Uma camada de tradução (microcódigo Cg/RSX para HLSL/SPIR-V) é
  inevitável; a tradução de RSX do ps3recomp é o componente que precisa cobrir
  isso.
- O esquema de permutação (`blinn_vert_default.0100.fp`, `.0111.fp`, …) indica
  que as variantes de shader são selecionadas por uma chave numérica. O
  renderizador precisa reproduzir essa seleção, ou a iluminação ficará errada
  mesmo que todo shader compile.

## Áudio

| Propriedade | Valor |
|---|---|
| Arquivos ADX | 23 (20 de música + 3 de efeitos/seletor) |
| Duração total dos ADX | 1.898,9 s ≈ 31,6 min |
| Canais | mono e estéreo |
| Taxa de amostragem | 44.100 Hz em todos os arquivos |
| Codificação | 4 bits, versão 3, tamanho de bloco 18 |
| Banco de vozes | `voice.afs`, 38.895.616 bytes |

Os cabeçalhos ADX são analisados de forma determinística, então o caminho de
áudio pode ser validado contra os comprimentos originais dos fluxos sem decodificar
uma única amostra.

## Arquivo principal: `rom.psarc`

O cabeçalho é analisado sem problemas:

| Campo | Valor |
|---|---|
| magic / versão | `PSAR` / `0x00010004` |
| compressão | `zlib` |
| extensão do cabeçalho | 31.708 bytes |
| tamanho / contagem de entradas de TOC | 30 / 218 |
| tamanho de bloco | 65.536 |

A tabela de conteúdo, porém, **não é legível com o layout documentado**:

- 0 de 32 entradas sondadas satisfazem `block_index < file_size / block_size`;
- não existe nenhum nome de entrada ASCII em toda a extensão de 31 KB do
  cabeçalho;
- a região não é um fluxo zlib nem deflate;
- sua entropia é de ~7,2 bits/byte, que não é nem estrutura de texto claro nem
  texto cifrado.

`skyclimax.psarc` portanto reporta `toc_state: "opaque"` e retorna uma lista de
entradas vazia. Adivinhar deslocamentos aqui corromperia silenciosamente toda
conclusão posterior, então a ferramenta se recusa. Esta é a maior lacuna não
resolvida da análise de assets: 96 % da carga do pacote está atualmente sem
índice.

## Localização

`USRDIR/string_array.bin` (35.472 bytes) e `USRDIR/lang/en/string_array.bin`
(26.944 bytes) começam com uma tabela de deslocamentos `u32` big-endian
(`0x00000CD0`, `0x00000CE0`, `0x00000CF0`, …), ou seja, um vetor de
deslocamentos para um bloco de strings. Apenas a árvore em inglês está presente
neste pacote.

## O que isso implica para o porte

1. **O renderizador precisa falar microcódigo Cg/RSX.** Não há código-fonte de
   shader para portar à mão.
2. **O áudio pode ser tratado como dado, não como código.** ADX/AFS são
   autodescritivos; o hospedeiro pode decodificá-los com uma biblioteca em vez
   de reimplementar o áudio de SPU do Cell.
3. **O pipeline de assets trava no `rom.psarc`.** Até que sua TOC seja legível,
   o conteúdo do maior arquivo — presumivelmente modelos, texturas e fases — é
   desconhecido, e nenhum trabalho de conversão de assets pode começar.
