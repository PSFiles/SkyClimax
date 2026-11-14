# Estado e registro de tarefas

Última atualização: 2026-11-14.

## Posição atual

**Marco alcançado: M3 — o pipeline de elevação está provado em um ELF de PS3
sintético.** O projeto é experimental. Não existe código recompilado do jogo, e
nada foi compilado.

| Marco | Estado | Bloqueio |
|---|---|---|
| M0 toolchain instalada e validada | validado | — |
| M1 pacote aberto, inventário reproduzível | validado | — |
| M2 contêiner do executável analisado | validado | carga criptografada |
| M3 pipeline de elevação provado em um ELF sintético | validado | — |
| M4 compilação nativa do código elevado | planejado | sem compilador C/C++ (KI-003) |
| M5 EBOOT descriptografado elevado | planejado | sem chave (KI-001) |
| M6 inicialização do runtime, primeiro quadro | planejado | depende de M4 e M5 |
| M7 jogável | planejado | depende de M6 |

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
| 2026-11-14 | Importar um ELF PPC64 no Ghidra | feito | `PowerPC:BE:64:default`, importação bem-sucedida |
| 2026-11-14 | Elevar um ELF de PS3 sintético para C++ | feito | 1 função → 1.117 linhas |
| 2026-11-14 | Descriptografar o EBOOT de varejo | bloqueado | exige chave do título ou dump descriptografado |
| 2026-11-14 | Compilar o C++ gerado | bloqueado | sem compilador no hospedeiro |

## Próximos passos, ordenados por risco e dependência

1. **Obter um `EBOOT.elf` descriptografado.** Todo o restante depende disso.
   Maior risco, maior valor. Aceitação: `e_machine = 21`,
   `e_entry = 0x4CDF00`, SHA-256 registrado.
2. **Instalar MSVC Build Tools, CMake e Ninja.** Desbloqueia o M4
   independentemente do passo 1 e pode ser feito em paralelo. Aceitação: `cl` e
   `cmake --version` funcionam, e a elevação sintética compila.
3. **Elevar a imagem real e contar funções.** Aceitação: carregador e liftedor
   concordam na contagem de funções, e não restam avisos
   `has no continuation`.
4. **Agrupar as importações de firmware por biblioteca.** Isso determina o
   escopo de HLE e, portanto, o cronograma real. Aceitação: uma tabela de
   biblioteca → contagem de NIDs na matriz de compatibilidade.
5. **Atacar a TOC do `rom.psarc`.** Necessário antes de qualquer conversão de
   assets. Abordagem: procurar o leitor no EBOOT descriptografado em vez de
   adivinhar o formato.
6. **Traduzir os 101 programas Cg.** Só faz sentido quando o renderizador rodar.

## O que deliberadamente não foi feito

- Nenhum nome de função, endereço ou lista de importações foi inventado para a
  imagem de varejo. A carga é criptografada; reportar tais dados seria
  fabricação.
- Nenhuma chave de descriptografia foi gerada, adivinhada ou embutida.
- Nenhum stub foi escrito para uma biblioteca que não tenha sido observada em
  uma tabela de importações real.
- Nenhum diretório `tools/` foi criado, porque nenhuma ferramenta auxiliar além
  de `scripts/` foi necessária; andaimes vazios não são progresso.

## Riscos

| Risco | Impacto | Mitigação |
|---|---|---|
| A descriptografia nunca fica disponível | o projeto não passa do M2 | documentar o requisito exato; manter todas as outras etapas testáveis sem ela |
| A TOC do `rom.psarc` continua ilegível | conversão de assets impossível | tratar como tarefa de pesquisa, não como bloqueio do trabalho de código |
| Cobertura da tradução Cg/RSX | a renderização não vai bater | partir da camada RSX do runtime compartilhado, não de um renderizador sob medida |
| Áudio dependente de SPU | o caminho de áudio pode exigir execução de SPU | ADX é autodescritivo; preferir decodificação no hospedeiro (ADR-0007) |
| Deriva do backend | a saída recompilada muda em silêncio | fixar o ps3recomp por commit; aplicar patch em vez de bifurcar |
