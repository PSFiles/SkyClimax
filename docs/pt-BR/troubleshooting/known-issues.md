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

**Severidade:** resolvido

**Observado.**

```text
cl      MISSING
cmake   MISSING
ninja   MISSING
gcc     MISSING
clang   MISSING
```

**Causa.** A estação de trabalho não tem o Visual Studio Build Tools instalado.

**Correção aplicada.** O Visual Studio Build Tools 2022 (17.14.45, MSVC
14.44.35207, SDK 10.0.26100.0) foi instalado, e o LLVM 23.1.5 fornece o
clang-cl, o único compilador que aceita o uso de `__atomic_*` e
`__builtin_bswap*` no cabeçalho gerado. `scripts/build.py` conduz o clang-cl e o
Ninja diretamente.

**Verificado.** As 24 unidades de tradução de PPU e as 5 de SPU compilam sem
erros, e o link produz `build/SkyClimax.exe` (295,6 MB).

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

**Severidade:** resolvido

**Observado.** `lib/ps3recomp_runtime.lib` exporta implementações HLE
(`cellAudioInit`, auxiliares de `cellGcmSys`, …), mas nenhum dos pontos de
entrada de inicialização. Procurar `load_elf` e `run` na biblioteca não retorna
nada, e o `main.cpp` do template do upstream declara que `ppu_load_elf`,
`ppu_recomp_register`, `ppu_hle_init`, `ppu_sysprx_register`, `ppu_fs_register`,
`lv2_init_syscalls` e `ppu_run` são "compiled into this project from
`PS3RECOMP_DIR`".

**Causa.** A v0.19.0 é publicada como release binária; as fontes do runtime e a
árvore `templates/project/` ficam no repositório do upstream, não no arquivo.

**Correção aplicada.** O repositório do upstream foi clonado em
`.vendor/ps3recomp-src` e posicionado em
`ae92407bb1d899e3d32143e360fe6e6d4d8fa1b5` — exatamente o commit registrado no
`VERSION.txt` da release. Ele fornece `runtime/ppu/ppu_loader.cpp`,
`ppu_hle.cpp`, `ppu_fs.cpp`, `ppu_sysprx.cpp`, `libs/*.c` e
`templates/project/`, que o `CMakeLists.txt` do template consome por
`PS3RECOMP_DIR`.

**Verificado.** `git log -1` reporta
`ae92407bb1d899e3d32143e360fe6e6d4d8fa1b5` e `runtime/ppu/` contém as quatro
fontes de inicialização. O link continua não testado porque falta o compilador
(KI-003).

## KI-010 — o título trava porque o handler de fila do GCM nunca é chamado

**Severidade:** bloqueante (M7)

**Observado.** Depois de quatro chamadas a `SetConvertAndFlip` o título bloqueia
para sempre em `sys_event_queue_receive` na fila que ele mesmo criou:

```text
[evt] queue_create -> id=1 key=0x8000CAFE02460300 size=2
[cellGcmSys] SetQueueHandler(00000000004D9558)
[WAIT] event_queue_receive(q=1 timeout=9000000) tid=3 cia=0x004E3480 lr=0x002C698C
```

A função do convidado em `0x002C68A0` monta a chave `0x8000CAFE02460300`, cria a
fila e então espera em um laço de 100 iterações com timeout de 9 s, destruindo a
fila em seguida. Ela espera pelo handler que registrou via
`cellGcmSetQueueHandler` (NID `0x0A862772`).

**Causa.** `libs/video/cellGcmSys.c` guarda o argumento em um ponteiro de função
do *hospedeiro* (`CellGcmQueueHandler`) e nunca o invoca. O próprio comentário do
upstream, na heurística de circulação da FIFO, afirma que o "caminho
SetQueueHandler / context-switch" não está modelado. O argumento passado pelo
jogo é um OPD do convidado, então chamá-lo como ponteiro do hospedeiro saltaria
para código do convidado.

**Hipótese testada e refutada.** O patch 0001 de `tools/patches/apply.py` mantém
o valor como OPD de convidado de 32 bits e o despacha por `g_ps3_guest_caller`
nos mesmos pontos em que o handler de flip dispara. Ele foi aplicado, o runtime
foi recompilado do código-fonte e o título se comportou de forma idêntica: 612
chamadas a `event_queue_receive` em 100 s, ainda travado. O patch foi revertido e
o script mantido apenas como registro do experimento.

**Medido com os diagnósticos do próprio runtime** (sem patch):

```bash
EVT_PUSHLOG=1 PS3_EVQSTAT=100 ./build/SkyClimax.exe .../EBOOT.elf
```

- `EVT_PUSHLOG=1` conta pushes para a fila 1: **0 em 60 s**.
- `PS3_WAITBT=1` despeja a pilha do convidado na espera: `tid=3 q=1`, `r3=1`,
  `r5=0x00895440` (9.000.000 µs), `lr=0x002C698C`, `r28=r29=r31=0x016EA508`.
- O build com patch foi testado de novo com `EVT_PUSHLOG=1`: **continua 0
  pushes**, então o handler de fila definitivamente não é o produtor.

**Conclusão, nos termos do próprio runtime.** O comentário dele sobre
`PS3_EVQSTAT` diz que pendente > 0 significa que o receptor não acorda (bug do
runtime) e pendente == 0 significa que nada produziu o evento. A contagem é zero,
então **nada nunca o produz**. O receptor não falha em acordar; ele espera por um
produtor que nunca executa.

**Qual é provavelmente o produtor.** Vinte e uma threads são criadas na mesma
janela, todas do middleware CRI: `CriThread` (várias), `CriSr_ProcessServer`,
operárias `CriThread`. A chave da fila `0x8000CAFE02460300` é o magic próprio da
CRI, então o produtor é um par servidor/cliente da CRI, não o callback do GCM nem
o cellAudio (que registrou chave `0x0`, correspondendo às filas 2 e 3, não à 1).

**O que o despejo de threads acrescentou.** Com `WAITBT_EVERY=1`, apenas duas
threads bloqueiam em fila: `tid=3` na `q=1` e `tid=1` na `q=3` (esta recebendo
eventos de SPU, `src=0xFFFFFFFF53505501`). As outras 19 threads estão vivas e nunca
tocam uma fila. Não há **nenhuma** espera de `lwmutex`, semáforo, variável de
condição, flag de evento ou porta de evento em todo o log, então as threads CRI não
estão bloqueadas em uma primitiva de sincronização que o runtime não implementa —
elas simplesmente não produzem.

**O lado SPU não é o problema.** A imagem do CRI Sound Renderer
(`fp=0x84857EC5B21E5F74`) é importada, elevada e executa:

```text
[SPU] thread_init group=0x1000 index=0 img=0x11528F08 -> tid=0x2000 entry=0x000000F0
[SPU] group_start id=0x1000 -> LIFTED SPU execution (image 516220944)
[SPU] tid=0x2000 RUNNING lifted image entry=0x000F0 (image 516220944)
```

Então o código de SPU elevado executa; o que falta é o servidor CRI do lado PPU
responder à própria fila.

**O re-lift com nomes identificou o subsistema.** Gerar `work/meta/names.json`
(281 funções nomeadas a partir de strings referenciadas) e re-elevar com `--names`
transformou os endereços em símbolos da CRI:

| Endereço | Nome | Papel |
|---|---|---|
| `0x002C68A0` | `mxr000` | mixer da CRI, a função que bloqueia |
| `0x002C410C` | `mxr004` | laço de polling em torno da espera (`lr=0x002C47B8` está dentro dele) |
| `0x002512E8` | `CriSr_ProcessServer` | thread servidora do sound renderer |
| `0x002356B8` | `CriAuVoice_Initialize` | inicialização de vozes |
| `0x00229654` | `CriAuFileLoader_Load` | carregador de streams |

Então a chamada que bloqueia é o **mixer da CRI esperando o sound renderer**, não
o renderer esperando o mixer.

**O renderer está ocioso, não girando.** `[spu] drain-resume return_pc=0x08274`
aparece 8 vezes em 60 s — o renderer elevado na SPU acorda, retorna e volta a
dormir. `[spu_workload] task 0 ... sleeping in WAIT_SIGNAL` concorda.

**Conclusão.** A inicialização de áudio da CRI entra em impasse: o mixer do lado
PPU bloqueia numa fila que o renderer da SPU deveria responder, e o renderer fica
ocioso esperando trabalho que nunca chega. Nenhum dos dois lados anda.

**Por que o re-lift não terminou o serviço.** `--names` emite o símbolo como
comentário acima da função, mas o corpo continua sendo tradução registrador a
registrador. `mxr000` são centenas de linhas de atribuições `ctx->gpr[n]`, então a
chamada de handshake que falta não se lê dali. Nomear respondeu *qual* subsistema,
não *qual* chamada.

**O que realmente terminaria.** Anexar um depurador: quebrar em
`sys_event_queue_push` para confirmar que nenhuma thread CRI chega lá e então
acompanhar a sequência de start do renderer. Isso exige sessão interativa, não mais
sondagem por script — as flags de ambiente estão esgotadas.
