# Matriz de compatibilidade

Três estados são usados de forma consistente: **planejado** (projetado, sem
código), **implementado** (o código existe), **validado** (exercitado com um
comando e um resultado registrados).

## Ferramentas de análise

| Capacidade | Estado | Evidência |
|---|---|---|
| Análise do cabeçalho PKG | validado | `skyclimax pkg-info`, 46 itens, tamanho igual ao do arquivo |
| Extração do PKG | validado | 46 arquivos extraídos, caminho rápido `(pycryptodome)` |
| Análise do cabeçalho SELF | validado | entrada `0x4CDF00`, 8 phdrs, `entry_in_data_segment: true` |
| Verificação do ELF descriptografado | validado | `e_machine=21`, `e_entry=0x4CDF00`, tamanho `0x5643B8` |
| Análise do PARAM.SFO | validado | `TITLE = After Burner Climax` |
| Variante FArc simples | validado | `SYSTEM.farc`, 2 registros, cargas PNG |
| Variante FArc comprimida | validado | `shader_cg.farc`, 101 registros, cargas gzip |
| Análise do cabeçalho ADX | validado | 23 arquivos, 44,1 kHz, 1.898,9 s no total |
| Análise do cabeçalho PSARC | validado | `PSAR`, `zlib`, 218 entradas de TOC |
| Análise da TOC do PSARC | bloqueado | `toc_state: opaque` (KI-002) |
| Inventário e hash | validado | `skyclimax inventory`, SHA-256 por arquivo |

## Pipeline de recompilação

| Capacidade | Estado | Evidência |
|---|---|---|
| Carga do ELF + resolução de OPD | validado | 11.827 descritores → 11.338 funções, TOC `0x4ed088` |
| Extração das importações de firmware | validado | 207 importações em 14 bibliotecas |
| Resolução de NIDs | validado | 163 de 207 nomeados pela base do kit |
| Desmontagem PPC64 | validado | 1.109.100 instruções decodificadas (90,9 % do texto) |
| Geração de C++ | validado | 15.237 funções, 17 blocos, 9.571.078 linhas |
| Completude da elevação | validado | 2 avisos em 15.237 funções, ambos no fim do segmento |
| Ligação das chamadas HLE | validado | 224 sítios `ps3_hle_call` no código gerado |
| Compilação do C++ | planejado | sem compilador (KI-003) |
| Link nativo | planejado | exige as fontes do runtime (KI-009) |
| Inicialização do runtime | planejado | depende dos dois anteriores |

## Ghidra

| Capacidade | Estado | Evidência |
|---|---|---|
| Inicialização headless | validado | banner de uso com JDK 25 |
| Importação de ELF PPC64 BE | validado | `PowerPC:BE:64:64-32addr` |
| Auto-análise completa | validado | 358 s, análise bem-sucedida |
| Exportação de funções/símbolos/strings | validado | 11.541 funções, 118.346 símbolos, 3.140 strings |

## REA

| Capacidade | Estado | Evidência |
|---|---|---|
| CLI executa | validado | `--version` → `6.9.0` |
| Relatório de capacidades | validado | relatório de 624 linhas, 4 provedores |
| Provedor Ghidra no Windows | indisponível para PPU | admissão apenas de PE (KI-005) |
| Fluxo de evidências | implementado | não exercitado com dados de PPU |

## Subsistemas do jogo

| Subsistema | Estado | Observação |
|---|---|---|
| Execução de PPU | planejado | código elevado, não compilado |
| Execução de SPU | planejado | `cellSpurs` 24 importações, `efc_smoke_job` presente |
| Renderização RSX / GCM | planejado | 101 programas Cg precisam ser traduzidos |
| Áudio (ADX/AFS) | planejado | decodificadores CRI presentes para PPU e SPU; decodificação no hospedeiro é preferível (ADR-0007) |
| Entrada (cellPad) | planejado | 6 importações, exportadas por `sys_io` |
| Sistema de arquivos (cellFs) | planejado | 19 importações `sys_fs`; camada de arquivos bloqueada pelo KI-002 |
| Dados salvos (cellSaveData) | planejado | não importado por este título |
| Troféus (NP) | planejado | `sceNpTrophy` 9 importações, `TROPHY.TRP` presente |
| Rede | planejado | `sceNp` 25, `cellNetCtl` 8 importações |

## Registro de validação

| Data | Comando | Resultado |
|---|---|---|
| 2026-11-14 | `pytest` | 22 aprovados (16 unitários, 6 de integração) |
| 2026-11-14 | `skyclimax self-info EBOOT.BIN` | 8 phdrs, entrada `0x4CDF00` |
| 2026-11-14 | `analyzeHeadless -import smoke.elf` | importação bem-sucedida |
| 2026-11-14 | `rea capabilities` | 4 provedores, Ghidra apenas PE no Windows |
| 2026-11-14 | `ppu_loader.py EBOOT.elf` | 11.338 funções, 207 importações |
| 2026-11-14 | `ghidra_analyze.py EBOOT.elf` | 11.541 funções, 358 s de análise |
| 2026-11-14 | `ppu_lifter.py EBOOT.elf` | 15.237 funções, 9m10s, 2 avisos |
