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
| Carga do ELF + resolução de OPD | validado (sintético) | `entry (OPD) 0x20000 -> code 0x10000, toc 0x20d00` |
| Desmontagem PPC64 | validado (sintético) | o liftedor consumiu a desmontagem |
| Geração de C++ | validado (sintético) | 1 função → 1.117 linhas |
| Compilação do C++ | planejado | sem compilador (KI-003) |
| Geração de stubs HLE | planejado | precisa de tabela de importações descriptografada |
| Link nativo | planejado | depende dos anteriores |

## Ghidra

| Capacidade | Estado | Evidência |
|---|---|---|
| Inicialização headless | validado | banner de uso com JDK 25 |
| Importação de ELF PPC64 BE | validado | `PowerPC:BE:64:default`, importação bem-sucedida |
| Análise do EBOOT real | bloqueado | carga criptografada (KI-001) |

## REA

| Capacidade | Estado | Evidência |
|---|---|---|
| CLI executa | validado | `--version` → `6.9.0` |
| Relatório de capacidades | validado | relatório de 624 linhas, 4 provedores |
| Provedor Ghidra no Windows | indisponível para PPU | admissão apenas de PE (KI-005) |
| Fluxo de evidências | implementado | não exercitado com dados de PPU |

## Subsistemas do jogo

Nada abaixo está implementado. A lista existe para tornar a lacuna explícita.

| Subsistema | Estado | Observação |
|---|---|---|
| Execução de PPU | planejado | depende da descriptografia |
| Execução de SPU | planejado | desconhecido até as importações serem legíveis |
| Renderização RSX / GCM | planejado | 101 programas Cg precisam ser traduzidos |
| Áudio (ADX/AFS) | planejado | tratado como dado (ADR-0007, proposto) |
| Entrada (cellPad) | planejado | |
| Sistema de arquivos (cellFs) | planejado | camada de arquivos bloqueada pelo KI-002 |
| Dados salvos (cellSaveData) | planejado | |
| Troféus (NP) | planejado | `TROPHY.TRP` presente |
| Rede | planejado | `NPWR00981` presente; escopo desconhecido |

## Registro de validação

| Data | Comando | Resultado |
|---|---|---|
| 2026-11-14 | `pytest` | 16 aprovados |
| 2026-11-14 | `skyclimax self-info EBOOT.BIN` | 8 phdrs, entrada `0x4CDF00` |
| 2026-11-14 | `analyzeHeadless -import smoke.elf` | importação bem-sucedida |
| 2026-11-14 | `rea capabilities` | 4 provedores, Ghidra apenas PE no Windows |
| 2026-11-14 | `ppu_lifter.py smoke.elf` | 1 função, 1.117 linhas |
