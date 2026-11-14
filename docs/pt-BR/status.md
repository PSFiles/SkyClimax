# Estado e registro de tarefas

Última atualização: 2026-11-14.

## Posição atual

**Marco alcançado: M6 — o executável recompilado inicializa e apresenta
quadros.** Não é jogável: o título carrega seus arquivos, sobe o renderizador e
então fica em espera ociosa, e o único dispositivo disponível neste hospedeiro é
o rasterizador por software.

| Marco | Estado | Observação |
|---|---|---|
| M0 toolchain instalada e validada | validado | clang-cl 23.1.5 + MSVC 14.44 + Ninja |
| M1 pacote aberto, inventário reproduzível | validado | 46 arquivos |
| M2 contêiner do executável analisado | validado | layout SELF + ELF |
| M3 pipeline de elevação provado em um ELF sintético | validado | 1 função |
| M4 compilação nativa do código elevado | validado | 24 UTs de PPU + 5 de SPU → executável de 295,6 MB |
| M5 EBOOT descriptografado elevado | validado | 15.237 funções |
| M6 inicialização do runtime, primeiro quadro | validado | quadros apresentados; conteúdo não verificado |
| M7 jogável | planejado | bloqueado pela espera ociosa e pela disponibilidade de GPU |

## Registro de tarefas

| Data | Tarefa | Estado | Evidência |
|---|---|---|---|
| 2026-11-14 | Instalar e validar a toolchain | feito | `scripts/verify-tools.ps1` → 6/6 OK |
| 2026-11-14 | Extrair e analisar o pacote | feito | 46 arquivos; leitores de `PARAM.SFO`, FArc, ADX, PSARC |
| 2026-11-14 | Verificar o ELF descriptografado fornecido pelo dono | feito | `e_machine=21`, `e_entry=0x4CDF00`, SHA-256 registrado |
| 2026-11-14 | Carregar a imagem real | feito | 11.338 funções, 207 importações / 14 bibliotecas |
| 2026-11-14 | Auto-análise do Ghidra | feito | 11.541 funções, 118.346 símbolos, 358 s |
| 2026-11-14 | Elevar a imagem real | feito | 15.237 funções, 9.571.078 linhas |
| 2026-11-14 | Compilar o código elevado | feito | 24 UTs, 0 erros, `SkyClimax.exe` 295,6 MB |
| 2026-11-14 | Elevar as imagens de SPU embutidas | feito | 3 imagens, fingerprint `9470BA4123AAAB63` |
| 2026-11-14 | Iniciar até o primeiro quadro | feito | init D3D12, `SetConvertAndFlip` ×4, TOC do `rom.psarc` lida |
| 2026-11-14 | Chegar à jogabilidade | bloqueado | fica ocioso em `event_queue_receive` |

## O que o log de inicialização prova

Citado de `work/reports/run2.log`:

```text
[ppu] loaded 2 PT_LOAD segments, entry OPD 0x004CDF00
[boot] dispatching entry OPD 0x004CDF00 (stack top 0x0FF00000)
[ppu] run: code 0x00010230, toc 0x004ED088, sp 0x0FEFFF20
[D3D12] Initialization complete (1280x720, 2 buffers, pipeline=ready)
[rsx] D3D12 backend init OK -- window open
[fs] open '/dev_bdvd/PS3_GAME/USRDIR/ps3/rom.psarc' -> fd 3
[fs] read fd=3 nbytes=48 -> 48 (magic=50534152, total=48)
[fs] read fd=3 nbytes=31676 -> 31676
[fs] open '/dev_bdvd/PS3_GAME/USRDIR/ps3/shader_cg.farc' -> fd 4
[cellResc] SetConvertAndFlip(src=260046848) -> flip
```

`50534152` é `PSAR`: o jogo abre o próprio arquivo de 407 MB e lê a tabela de
conteúdo que este projeto não conseguiu analisar estaticamente. A camada de
arquivos do runtime, o fluxo de comandos RSX, o `cellResc` e o `cellSpurs` estão
todos ativos.

## Limitações conhecidas neste marco

- **Sem GPU de hardware neste hospedeiro.** O D3D12 cai para o WARP ("Microsoft
  Basic Render Driver"), então nada aqui diz sobre desempenho ou correção de
  renderização.
- **Sem dispositivo de áudio.** O `cellAudio` registra `Failed to get default
  audio endpoint` e continua em silêncio.
- **O título fica ocioso.** Depois dos flips ele bloqueia em
  `event_queue_receive` (`cia=0x004E3480`), que é o laço de eventos do
  cellSysutil esperando um evento que nunca chega.
- **O código de PPU está compilado em `/Od`.** Este hospedeiro tem 7,9 GB de RAM
  e uma UT de 600 mil linhas em `/O1` precisa de ~2,5 GB e ~10 minutos; a
  compilação pagina demais. Recompile com `scripts/build.py --optimize` em uma
  máquina com mais memória.

## Próximos passos, ordenados por risco e dependência

1. **Descobrir por que o laço de eventos nunca recebe.** Inspecionar o callback
   do convidado registrado por `cellSysutilRegisterCallback` (`func=0x004D7060`)
   e se o runtime chega a disparar o slot 0. Aceitação: o log avança além de
   `event_queue_receive` sem estourar o tempo limite.
2. **Verificar o conteúdo do quadro.** Capturar a superfície apresentada e
   comparar com uma execução de referência. Aceitação: um quadro não preto com a
   saída do próprio título.
3. **Executar em uma máquina com GPU** para que o D3D12 use hardware e o caminho
   RSX seja exercitado de verdade.
4. **Recompilar otimizado** assim que o título avançar, para ver se o `/Od` é
   ele mesmo a causa da parada.
5. **Reelevar com os nomes do Ghidra** (1.289 símbolos do motor já extraídos)
   para que o código gerado fique legível durante a depuração do passo 1.
