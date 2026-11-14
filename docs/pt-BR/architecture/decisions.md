# Registro de decisões

Cada registro declara a decisão, a evidência por trás dela e o que a tornaria
errada. Novos registros são acrescentados; os existentes não são reescritos.

## ADR-0001 — Usar o ps3recomp como backend de recompilação

**Status:** aceito

**Contexto.** Existem nove projetos de referência; dois nomeiam o ps3recomp
explicitamente como motor, e o próprio ps3recomp traz carregador, liftedor,
gerador de stubs e uma biblioteca de runtime para Windows.

**Decisão.** O SkyClimax vendoriza o ps3recomp v0.19.0 e acrescenta apenas
análise e código de compatibilidade específicos do jogo.

**Consequências.** Bugs do upstream são herdados e precisam de contornos
documentados. Em troca, o projeto começa com um liftedor funcionando em vez de
começar com um arquivo em branco.

**Falsificado se** o ps3recomp não conseguir expressar uma construção
necessária (por exemplo, uma instrução PPU que ele não eleva) e a lacuna não
puder ser fechada por um patch.

## ADR-0002 — Nunca adivinhar conteúdo criptografado

**Status:** aceito

**Contexto.** Os segmentos de `EBOOT.BIN` e a tabela de conteúdo de
`rom.psarc` são opacos. É fácil produzir listas de funções ou índices de
arquivo plausíveis e completamente fictícios.

**Decisão.** Os analisadores reportam um estado explícito
(`toc_state: "opaque"`) e retornam resultados vazios em vez de heurísticas. A
documentação declara o bloqueio e a evidência (valores de entropia, sondagens de
layout que falharam).

**Consequências.** O projeto parece menos completo do que uma versão fabricada
pareceria, e é exatamente esse o ponto: cada número na documentação pode ser
rastreado até um comando.

**Falsificado se** nunca — esta é uma regra de processo, não uma hipótese
técnica.

## ADR-0003 — Manter as árvores en-US e pt-BR paralelas byte a byte

**Status:** aceito

**Contexto.** Documentação bilíngue apodrece imediatamente se nenhuma máquina a
verificar.

**Decisão.** `scripts/check_docs_parity.py` compara conjuntos de arquivos, a
estrutura de títulos, a contagem de blocos de código, o corpo dos blocos de
código para linguagens de código e os links relativos, e valida o índice em
`docs/README.md`. A CI o executa em cada push.

**Consequências.** Uma tradução não pode ficar "quase pronta": um título ausente
quebra a build.

## ADR-0004 — Não distribuir chaves nem cargas descriptografadas

**Status:** aceito

**Contexto.** O repositório é público.

**Decisão.** O `.gitignore` exclui `*.pkg`, `*.rap`, `*.elf`, `*.self`, `work/`,
`.tools/`, `.vendor/` e qualquer arquivo `keys`. A documentação explica como o
dono produz uma imagem descriptografada localmente.

**Consequências.** Um clone novo não consegue executar o jogo; consegue
reproduzir cada etapa de análise, dado o pacote de varejo.

## ADR-0005 — Tratar o REA como camada de orquestração, não como analisador de PS3

**Status:** aceito

**Contexto.** O relatório de capacidades do próprio REA 6.9.0 declara,
literalmente: *"Windows Ghidra P0 accepts native x86, x86-64, ARMNT (Thumb-2) and
ARM64 PE applications and DLLs, DOS MZ images, and explicitly selected raw 6502
images"*. Um executável PPU de PS3 é um ELF PPC64 big-endian, que não está nesse
conjunto.

**Decisão.** O Ghidra é conduzido diretamente por `analyzeHeadless` para o
trabalho de PPU. O REA permanece instalado e é usado para registro de evidências
e para análise em hospedeiros cujo provedor Ghidra aceite ELF.

**Consequências.** O projeto não depende do REA em seu caminho crítico, o que
também faz com que ele continue funcionando se o REA mudar sua política de
admissão.

**Falsificado se** o provedor Windows do REA passar a aceitar ELF/PPC64; nesse
caso o ADR-0005 pode ser substituído.

## ADR-0006 — A seleção de variante do FArc é hipótese validada, não fato

**Status:** aceito

**Contexto.** Existem apenas duas amostras de FArc no pacote, e elas diferem na
caixa do quarto byte de magic e na largura do registro.

**Decisão.** Selecionar o layout do registro a partir do byte de magic e então
validar cada registro contra os limites do arquivo; levantar erro em caso de
incompatibilidade em vez de truncar.

**Consequências.** Se uma terceira variante aparecer, o analisador falha
ruidosamente em vez de analisar errado em silêncio.

## ADR-0007 — O áudio é tratado como dado, não como código de SPU

**Status:** proposto

**Contexto.** Todos os 23 fluxos de música/efeito são CRI ADX com cabeçalhos
autodescritivos; a voz é um banco CRI AFS. Nada disso exige execução de SPU do
Cell se o hospedeiro decodificar os fluxos por conta própria.

**Decisão (proposta).** Decodificar ADX/AFS no hospedeiro e expô-los pela
superfície HLE de `cellAudio`, em vez de elevar as tarefas de áudio de SPU do
jogo.

**Consequências.** Requer um decodificador ADX funcional no hospedeiro, o que é
bem compreendido. Não ajuda se o jogo também usar SPU para mixar efeitos que não
estão nos dados ADX.

**Falsificado se** o jogo conduzir o áudio por tarefas de SPU cuja saída não seja
um fluxo ADX direto.
