# Projetos de referência

Os metadados abaixo foram obtidos da API do GitHub em 2026-11-14 e são citados,
não inferidos. Cada projeto foi avaliado por arquitetura, não copiado.

| Repositório | Linguagem principal | Último push | Descrição (literal) |
|---|---|---|---|
| `sp00nznet/ps3recomp` | C | 2026-11-06 | Static recompilation runtime libraries for PlayStation 3 titles. |
| `n0madic/Soulcalibur2HD-recomp` | C | 2026-10-26 | Soulcalibur II HD native recompilation |
| `soyjxck/dod3-recomp` | C++ | 2026-11-03 | Drakengard 3 (PS3) static recompilation using ps3recomp |
| `whompay/inFAMOUSreborn` | C | 2026-11-12 | (sem descrição) |
| `WK2D/White-Knight-Chronicles-2-Recomp` | C++ | 2026-10-22 | Native C/C++ recompilation for White Knight Chronicles II (PS3). |
| `SulphurS16/ACFA-Port` | C++ | 2026-11-04 | Unofficial native Windows port of ARMORED CORE for Answer (PS3), built from your own copy of the game. |
| `SulphurS16/AC4-Port` | C++ | 2026-10-29 | Unofficial native Windows port of ARMORED CORE 4 (PS3), built from your own copy of the game. |
| `kastieloficial/RE-Code-Veronica-PS3-HD-Recomp-PC` | C | 2026-11-13 | Resident Evil Code: Veronica X HD - PS3 static recompilation port (hobby, no game data) |
| `timboat/demons-souls-recomp` | Python | 2026-11-13 | Native Windows port of Demon's Souls (PS3, BLUS-30443) via ps3recomp static recompilation. |
| `morluto/rea` | TypeScript | 2026-11-14 | Reverse engineer anything with agents, from app behavior down to native binaries. |

## O que os metadados já mostram

1. **Dois projetos nomeiam o ps3recomp como motor** (`dod3-recomp`,
   `demons-souls-recomp`). Somado ao fato de o próprio `ps3recomp` ser o runtime
   em C contra o qual os outros portes linkam, o ecossistema convergiu em um
   único backend em vez de um recompilador por jogo.
2. **A linguagem do hospedeiro é C ou C++** em oito de nove portes, o que é
   coerente com um pipeline cuja saída é C++ gerado e compilado por uma
   toolchain nativa.
3. **Python aparece como linguagem de orquestração** (`demons-souls-recomp`),
   consistente com o fato de as ferramentas do ps3recomp serem scripts Python
   que conduzem uma compilação CMake.
4. **Todos os repositórios estão ativos** (último push dentro do mês anterior à
   coleta), então as ferramentas ainda mudam. Fixar versões não é opcional para
   reprodutibilidade.

## Técnicas reutilizáveis

- **Fronteiras de função guiadas por OPD.** O ps3recomp documenta que a seção
  `.opd` fornece uma lista autoritativa de funções, muito mais confiável do que
  procurar prólogos. O SkyClimax adota isso: o ponto de entrada de `EBOOT.BIN`
  é `0x4CDF00`, dentro do segmento de dados, que é exatamente o layout de OPD
  que essa técnica pressupõe.
- **Módulos HLE indexados por NID.** Todo porte precisa de `cellGcmSys`,
  `cellAudio`, `cellPad`, `cellFs`, `cellSysutil` e afins. Implementá-los uma
  vez, indexados pelo NID de 32 bits, é a única abordagem viável.
- **Distribuição no modelo "traga seu próprio jogo".** Todo porte entrega
  apenas código. O SkyClimax segue a mesma regra: nenhum byte proprietário no
  repositório.
- **ELF sintético de fumaça como teste de pipeline.** O ps3recomp traz
  `make_smoke_elf.py`; o SkyClimax o usa para provar que o caminho de elevação
  funciona antes de o binário real estar disponível.

## Técnicas deliberadamente não adotadas

- **Backends gráficos escritos à mão por jogo.** `ACFA-Port` e `AC4-Port` são
  portes de dois jogos de um mesmo motor; o trabalho compartilhado é a camada do
  motor, não um renderizador sob medida por título. O SkyClimax mantém a
  tradução de RSX no runtime compartilhado e mantém código específico de jogo
  fora dele.
- **Interpretação de código PPU em tempo de execução.** Isso é um emulador, não
  uma recompilação estática, e contradiz o objetivo do projeto.
- **Commitar assets descriptografados ou chaves.** Nenhum projeto de referência
  faz isso, e fazê-lo tornaria o repositório impublicável.

## Questão em aberto levada adiante

Nenhum dos projetos de referência documenta um porte de After Burner Climax, e o
título é uma conversão de arcade da Sega AM2 de 2010, não um jogo de PhyreEngine
ou Unreal. Sua pilha de middleware (Sega `FArc`, CRI `ADX`, shaders Cg) precisa,
portanto, ser caracterizada a partir do próprio pacote, que é o que a
[análise de assets](../analysis/assets.md) faz.
