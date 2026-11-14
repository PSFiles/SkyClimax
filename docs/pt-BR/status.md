# Estado e registro de tarefas

Última atualização: 2026-11-14.

## Posição atual

**Marco alcançado: M5 — o executável descriptografado está carregado e elevado.**
O projeto é experimental. 15.237 funções foram traduzidas para C++, mas nada foi
compilado e nada foi executado.

| Marco | Estado | Bloqueio |
|---|---|---|
| M0 toolchain instalada e validada | validado | — |
| M1 pacote aberto, inventário reproduzível | validado | — |
| M2 contêiner do executável analisado | validado | — |
| M3 pipeline de elevação provado em um ELF sintético | validado | — |
| M4 compilação nativa do código elevado | planejado | sem compilador (KI-003), sem fontes do runtime (KI-009) |
| M5 EBOOT descriptografado elevado | validado | — |
| M6 inicialização do runtime, primeiro quadro | planejado | depende de M4 |
| M7 jogável | planejado | depende de M6 |

M4 e M5 são independentes: elevar não precisa de compilador, e compilar não
precisa de mais análise. M5 terminou primeiro porque o dono forneceu a imagem
descriptografada.

## Registro de tarefas

| Data | Tarefa | Estado | Evidência |
|---|---|---|---|
| 2026-11-14 | Instalar e validar Ghidra, JDK, Node, REA e a pilha Python | feito | `scripts/verify-tools.ps1` → 6/6 OK |
| 2026-11-14 | Analisar o cabeçalho do pacote de varejo | feito | `pkg-info`: 46 itens, `total_size` == tamanho do arquivo |
| 2026-11-14 | Extrair o pacote | feito | 46 arquivos, 551 MB |
| 2026-11-14 | Analisar o PARAM.SFO | feito | `TITLE = After Burner Climax`, `TITLE_ID = NPUB30151` |
| 2026-11-14 | Analisar o contêiner SELF | feito | entrada `0x4CDF00`, 8 phdrs, `retail_encrypted: true` |
| 2026-11-14 | Caracterizar o Sega FArc (ambas as variantes) | feito | 2 + 101 registros, cargas gzip |
| 2026-11-14 | Caracterizar o áudio CRI ADX | feito | 23 arquivos, 44,1 kHz, 1.898,9 s |
| 2026-11-14 | Sondar a tabela de conteúdo do PSARC | bloqueado | 0/32 entradas plausíveis → `opaque` |
| 2026-11-14 | Elevar um ELF de PS3 sintético para C++ | feito | 1 função → 1.117 linhas |
| 2026-11-14 | Verificar o ELF descriptografado fornecido pelo dono | feito | `e_machine=21`, `e_entry=0x4CDF00`, SHA-256 registrado |
| 2026-11-14 | Carregar a imagem real | feito | 11.827 OPDs → 11.338 funções, TOC `0x4ed088` |
| 2026-11-14 | Extrair e resolver as importações de firmware | feito | 207 importações, 14 bibliotecas, 163 NIDs nomeados |
| 2026-11-14 | Auto-análise do Ghidra na imagem real | feito | 11.541 funções, 118.346 símbolos, 358 s |
| 2026-11-14 | Elevar a imagem real | feito | 15.237 funções, 9m10s, 2 avisos |
| 2026-11-14 | Identificar motor e middleware pelas strings | feito | AM2 motion, AET, CRI 3.44.03, ENEPACK |
| 2026-11-14 | Compilar o C++ gerado | bloqueado | sem compilador no hospedeiro |
| 2026-11-14 | Linkar contra o runtime | bloqueado | fontes do runtime ausentes da release binária |

## Próximos passos, ordenados por risco e dependência

1. **Instalar MSVC Build Tools, CMake e Ninja.** Desbloqueia o M4. Aceitação:
   `cl` e `cmake --version` funcionam.
2. **Obter as fontes do runtime do kit.** A release binária traz cabeçalhos e
   `ps3recomp_runtime.lib`, mas não `ppu_load_elf`, `ppu_recomp_register`,
   `ppu_hle_init` nem `ppu_run`; o template de projeto do upstream os linka a
   partir de `PS3RECOMP_DIR`. Aceitação: um projeto que resolva esses símbolos.
3. **Compilar os 17 blocos gerados.** Espere tempos longos de compilação:
   9,57 M linhas. Aceitação: objetos produzidos sem erros, ou uma lista
   documentada dos que falham.
4. **Iniciar até o primeiro quadro.** Aceitação: um quadro capturado, não uma
   linha de log.
5. **Reelevar com os nomes do Ghidra.** 1.289 símbolos do motor já foram
   extraídos; passá-los por `--names` torna o código gerado legível. Faça isso
   depois da primeira compilação bem-sucedida, para o diff continuar revisável.
6. **Atacar a TOC do `rom.psarc`.** Necessário antes de qualquer conversão de
   assets. O leitor agora é localizável na imagem descriptografada, em vez de
   adivinhado.

## O que deliberadamente não foi feito

- Nenhum nome de função, endereço ou lista de importações foi inventado. Cada
  número da documentação remete a um comando do registro de validação.
- Nenhum stub foi escrito para uma biblioteca que o runtime já implementa.
- O C++ gerado não foi editado à mão; ele é regenerado a cada elevação.
- Nenhum byte do jogo foi comitado. A imagem descriptografada fica em
  `work/game/`, que está no `.gitignore`.

## Riscos

| Risco | Impacto | Mitigação |
|---|---|---|
| 9,57 M linhas podem exceder limites do compilador | a compilação falha de formas inesperadas | dividir mais com `--chunks`; `/bigobj` no MSVC |
| `cellSpurs` é apenas Partial no upstream | tarefas de SPU podem não rodar | isolar cedo o caminho do `efc_smoke_job` |
| A TOC do `rom.psarc` continua ilegível | conversão de assets impossível | tarefa de pesquisa, não bloqueio de código |
| Cobertura da tradução Cg/RSX | a renderização não vai bater | partir da camada RSX do runtime compartilhado |
| 2 avisos de elevação no fim do segmento | possíveis funções de cauda truncadas | inspecionar `func_00380E00` e `func_004B6F60` |
