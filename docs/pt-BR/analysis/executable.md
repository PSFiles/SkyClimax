# Análise do executável

Fonte: um `EBOOT.elf` descriptografado, fornecido localmente pelo dono do
projeto, 5.653.432 bytes, SHA-256
`d3a13dd3eeb388e61cfec72a507821b018fa9cafe01e520982cfc30d6d33b777`.

O arquivo só foi aceito depois de coincidir com a declaração do próprio
contêiner criptografado: `e_machine = 21` (`EM_PPC64`), `e_type = 2`
(`ET_EXEC`), `e_entry = 0x4CDF00`, 8 cabeçalhos de programa, 31 cabeçalhos de
seção e tamanho igual ao campo `elf_size` do cabeçalho SELF (`0x5643B8`).

Reproduza com:

```bash
python -m skyclimax self-info work/pkg/USRDIR/EBOOT.BIN
python .vendor/ps3recomp/tools/ppu_loader.py work/game/EBOOT.elf -o work/meta
```

## Contêiner

| Campo | Valor |
|---|---|
| magic | `SCE\0` |
| versão do SELF | 2 |
| revisão de chave | 1 (varejo, assinado e criptografado) |
| tamanho dos metadados | 1.184 |
| extensão do cabeçalho | 2.688 (`0xA80`) |
| tamanho do ELF contido | 5.653.432 (`0x5643B8`) |
| cabeçalhos de programa | 8 |
| cabeçalhos de seção | 31 |

## Cabeçalho ELF embutido

| Campo | Valor | Significado |
|---|---|---|
| classe | 2 | ELF64 |
| dados | 2 | big-endian |
| OSABI | `0x66` | PlayStation 3 |
| `e_type` | 2 | `ET_EXEC` — endereço de carga fixo, sem relocações |
| `e_machine` | 21 | `EM_PPC64` |
| `e_entry` | `0x4CDF00` | descritor OPD, não código |
| `e_flags` | 0 | |

## Cabeçalhos de programa

| # | tipo | perms | vaddr | filesz | memsz | bss |
|---|---|---|---|---|---|---|
| 0 | `PT_LOAD` | R+X | `0x10000` | `0x4A7060` | `0x4A7060` | 0 |
| 1 | `PT_LOAD` | R+W | `0x4C0000` | `0xB1B14` | `0x12554A8` | `0x11A3994` |
| 2 | `PT_LOAD` | R | 0 | 0 | 0 | 0 |
| 3 | `PT_LOAD` | R+W | 0 | 0 | 0 | 0 |
| 4 | `PT_LOAD` | R+W | 0 | 0 | 0 | 0 |
| 5 | `PT_TLS` | R | `0x4EF27C` | 4 | `0x1EC` | `0x1E8` |
| 6 | `0x60000001` | – | `0x4B7000` | `0x20` | `0x20` | 0 |
| 7 | `0x60000002` | – | `0x4B7020` | `0x40` | `0x40` | 0 |

O ponto de entrada fica no cabeçalho de programa 1, que é `R+W` e não
executável — o layout clássico de OPD. Resolvê-lo produz:

```text
entry (OPD)      : 0x4cdf00 -> code 0x10230, toc 0x4ed088
module TOC (r2)  : 0x4ed088
OPD region       : 0x4cdef0 size 0x17198
```

As primeiras instruções de `0x10230` confirmam: `li r2,0; oris r2,r2,0x4c;
ori r2,r2,0xdf00; lwz r2,4(r2)` carrega a palavra de TOC de `OPD+4`.

## Estado da descriptografia

Descriptografado pelo dono, fora deste repositório. A carga foi verificada antes
do uso:

| Verificação | Observado |
|---|---|
| entropia do segmento 0, primeiros 64 KiB, enquanto criptografado | 7,9973 bits/byte |
| instruções decodificáveis em `.text` | 1.109.100 de 1.219.608 palavras (90,9 %) |
| tabela de funções | não vazia, 11.338 entradas únicas |

Os 9,1 % restantes do segmento de texto são dados e preenchimento de alinhamento
intercalados com código, o que é normal para esta toolchain.

## Inventário de funções

| Métrica | Valor | Origem |
|---|---|---|
| descritores OPD | 11.827 | `ppu_loader.py` |
| funções únicas (derivadas de OPD) | 11.338 | `ppu_loader.py` |
| funções após análise do Ghidra | 11.541 | `ghidra_analyze.py` |
| símbolos | 118.346 | `ghidra_analyze.py` |
| strings referenciadas | 3.140 | `ghidra_analyze.py` |
| funções emitidas pelo liftedor | 15.237 | `ppu_lifter.py` |
| destinos de chamada únicos | 5.678 | `ppu_lifter.py` |

O liftedor emite mais funções que a tabela de OPD porque também cria
envoltórios de entrada por cauda (3.397 deles) para endereços alcançados apenas
por chamadas de cauda.

## Importações de firmware

207 importações em 14 bibliotecas:

| Biblioteca | Funções |
|---|---|
| `sysPrxForUser` | 32 |
| `cellGcmSys` | 27 |
| `sceNp` | 25 |
| `cellSpurs` | 24 |
| `cellSysutil` | 23 |
| `sys_fs` | 19 |
| `cellResc` | 12 |
| `cellAudio` | 11 |
| `sceNpTrophy` | 9 |
| `cellNetCtl` | 8 |
| `sys_io` | 6 |
| `cellGame` | 6 |
| `cellSync` | 3 |
| `cellSysmodule` | 2 |

Resolver os NIDs contra a base de dados do kit nomeia 163 de 207; os 44
restantes estão ausentes daquela base, não são desconhecidos do jogo.

**Os nomes de biblioteca vêm da tabela libstub e são autoritativos.** A base de
NIDs registra nomes canônicos de módulo, que diferem: as seis funções de
`cellPad` são exportadas por `sys_io`, e dezesseis funções de `cellFs` por
`sys_fs`. Ler apenas a base de NIDs concluiria, erradamente, que o título não tem
suporte a controle.

## Perfil de instruções

Medido sobre o segmento de texto com capstone (PPC64, big-endian),
ressincronizando após palavras não decodificáveis:

| Grupo | Participação |
|---|---|
| inteiro | 31,8 % |
| carga/armazenamento | 27,5 % |
| desvio | 12,2 % |
| ponto flutuante | 7,9 % |
| vetorial (VMX) | 1,3 % |
| outros | 19,3 % |

Mnemônicos mais frequentes: `lwz` 8,3 %, `stw` 6,1 %, `addi` 4,9 %, `ld` 4,6 %,
`li` 4,4 %, `mr` 3,9 %, `bl` 3,8 %, `clrldi` 3,8 %. Há 42.620 chamadas diretas
`bl`.

A baixa participação de VMX (1,3 %) é notável: este título não é pesado em
vetores, então os casos-limite de paired-single e VMX128 que dominam outros
portes de PS3 ficam menos expostos aqui. Isso é uma observação sobre contagens
estáticas de instruções, não uma garantia sobre quais instruções executam.

## Identificação do motor

Recuperada de strings referenciadas, não adivinhada:

| Evidência | Significado |
|---|---|
| `AM2M_InitMotionWorkEx` | biblioteca de movimento da Sega AM2 |
| `extract_aet_node` | formato de partículas/efeitos AET da Sega |
| `create_aircraft`, `set_object_node_matrix`, `load_objset_texture`, `create_object_index_buffer` | subsistema de modelos/objset |
| `evt_init_pursuit_emy`, `evt_init_search_light`, `evt_init_fly_xb70_kill` | scripts de eventos de missão |
| `efc_smoke_job`, `efc_smoke_buff`, `efc_cloud_buff` | tarefa e buffers de efeito na SPU |
| `CRI Audio/PS3PPU Ver.3.44.03`, `CRI ADX Decoder/PS3SPU Ver.1.00.07` | middleware CRI, compilado em 2009-10-30 |
| `ENEPACK_ERROR_*` | códigos de erro da biblioteca de empacotamento da Sega |

`efc_smoke_job` importa para o escopo: o título executa ao menos uma tarefa
SPURS para efeitos de fumaça, então a execução de SPU não se limita ao áudio. O
áudio em si é o decodificador da própria CRI (presente para PPU e para SPU), o
que sustenta decodificar ADX no hospedeiro em vez de executar o caminho de áudio
da SPU (ADR-0007).

## Próximo passo

As fontes elevadas estão completas, mas nada foi compilado. Compilar exige duas
coisas que não estão na release binária: uma toolchain C/C++ e as fontes do
runtime do kit (`ppu_load_elf`, `ppu_recomp_register`, `ppu_hle_init`,
`ppu_run`), que o template de projeto linka a partir de `PS3RECOMP_DIR`. Veja
[o guia de compilação](../build/build.md).
