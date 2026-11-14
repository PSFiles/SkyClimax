# Problemas conhecidos

Cada entrada registra o erro exato observado, a causa e o contorno, ou a razão
de não existir nenhum.

## KI-001 — A carga do EBOOT está criptografada

**Severidade:** bloqueante (M5)

**Observado.** `skyclimax self-info` reporta `retail_encrypted: true`. Os
primeiros 64 KiB do segmento 0 têm entropia de 7,9973 bits/byte e não contêm
instruções legíveis. `unfself.py --info` imprime `key_revision : 0x0001 (RETAIL
- encrypted)`.

**Causa.** Segmentos SELF de varejo são criptografados com AES usando uma chave
por título que não é derivável a partir do pacote.

**Contorno.** Nenhum implementado, por decisão de projeto (ADR-0002, ADR-0004).
O dono precisa fornecer a chave do título ou um executável despejado de uma
cópia em execução.

**Não** substitua a desmontagem dos dados cifrados por heurística; isso produz
lixo de aparência plausível.

## KI-002 — A tabela de conteúdo do `rom.psarc` é opaca

**Severidade:** bloqueante (pipeline de assets)

**Observado.** O cabeçalho é analisado; `toc_state` é `opaque`, com 0 de 32
entradas sondadas consistentes com o layout documentado.

**Causa.** Desconhecida. A região não é texto claro, nem zlib, nem deflate; sua
entropia (~7,2 bits/byte) descarta tanto uma leitura ingênua quanto AES simples.

**Contorno.** Nenhum. `skyclimax.psarc` retorna uma lista de entradas vazia em
vez de adivinhar.

## KI-003 — Não há toolchain C/C++ neste hospedeiro

**Severidade:** bloqueante (M4)

**Observado.**

```text
cl      MISSING
cmake   MISSING
ninja   MISSING
gcc     MISSING
clang   MISSING
```

**Causa.** A estação de trabalho não tem o Visual Studio Build Tools instalado.

**Contorno.** Instale o VS Build Tools 2022 com "Desktop development with C++".
Até lá, o C++ elevado é verificado estruturalmente (não vazio, uma função por
função do convidado, auxiliares de prólogo/epílogo esperados presentes), mas
nunca compilado.

## KI-004 — O Ghidra 12.2 rejeita o JDK 21

**Severidade:** resolvido

**Observado.**

```text
WARNING: JAVA_HOME environment specifies unsupported java version
ERROR: Unable to prompt user for JDK path, no TTY detected.
```

**Causa.** `application.java.min=25`.

**Correção.** Instalar o Temurin 25 e exportar `JAVA_HOME` para ele. Verificado:
o banner do headless é impresso e um ELF PPC64 é importado com a linguagem
`PowerPC:BE:64:default`.

## KI-005 — O provedor Ghidra do REA no Windows aceita apenas PE

**Severidade:** limitação (fluxo de análise)

**Observado.** `rea capabilities` reporta, literalmente: *"Windows Ghidra P0
accepts native x86, x86-64, ARMNT (Thumb-2) and ARM64 PE applications and DLLs,
DOS MZ images, and explicitly selected raw 6502 images; managed, hostile,
sensitive, and mutable-path targets are unsupported."*

**Causa.** A ponte do Windows tem como alvo binários PE nativos.

**Contorno.** Conduzir o Ghidra headless diretamente para análise de ELF de PPU
(ADR-0005), ou executar o REA em Linux/macOS, onde seu provedor Ghidra aceita
ELF.

## KI-006 — O npm não cria um atalho em `.bin` com `--prefix`

**Severidade:** resolvido

**Observado.** `.tools/rea/node_modules/.bin/rea: No such file or directory`
após uma instalação bem-sucedida.

**Causa.** `npm install --prefix` sem um `package.json` no prefixo não cria
links de binários.

**Correção.** Invocar o script de entrada diretamente:
`node .tools/rea/node_modules/rea-agents/scripts/rea.mjs`.

## KI-007 — `pkg_extract.py` precisa de `pycryptodome` para velocidade aceitável

**Severidade:** resolvido

**Observado.** Sem `pycryptodome`, o extrator cai para uma implementação de AES
em Python puro e um pacote de 551 MB leva um tempo extremamente longo.

**Correção.** `pip install pycryptodome` em `.venv` (faz parte das dependências
de desenvolvimento). O extrator imprime `(pycryptodome)` quando o caminho rápido
está ativo.

## KI-008 — O `info_size` do PKG não bate com o `item_count`

**Severidade:** cosmética (questão em aberto)

**Observado.** `info_offset = 192`, `info_size = 8`, `item_count = 46`. Uma
tabela plana de `{u32 id, u32 size}` com 46 entradas teria 368 bytes e se
estenderia além de `data_offset = 384`.

**Estado.** Não resolvido. Os campos do cabeçalho são reportados brutos; a
enumeração de entradas é delegada ao extrator do ps3recomp, cujo resultado de 46
arquivos valida `item_count` de forma cruzada.

## KI-009 — a release binária omite as fontes do runtime

**Severidade:** bloqueante (M4)

**Observado.** `lib/ps3recomp_runtime.lib` exporta implementações HLE
(`cellAudioInit`, auxiliares de `cellGcmSys`, …), mas nenhum dos pontos de
entrada de inicialização. Procurar `load_elf` e `run` na biblioteca não retorna
nada, e o `main.cpp` do template do upstream declara que `ppu_load_elf`,
`ppu_recomp_register`, `ppu_hle_init`, `ppu_sysprx_register`, `ppu_fs_register`,
`lv2_init_syscalls` e `ppu_run` são "compiled into this project from
`PS3RECOMP_DIR`".

**Causa.** A v0.19.0 é publicada como release binária; as fontes do runtime e a
árvore `templates/project/` ficam no repositório do upstream, não no arquivo.

**Contorno.** Clonar o repositório do upstream no commit fixado e apontar
`PS3RECOMP_DIR` para ele, ou obter um tarball de fontes do mesmo commit. Até lá,
o código elevado pode ser gerado, mas não linkado.
