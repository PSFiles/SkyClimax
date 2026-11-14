# AGENTS.md

Instruções para qualquer agente ou colaborador que trabalhe neste repositório.
Leia este arquivo por completo antes de alterar qualquer coisa.

English (en-US): [AGENTS.md](AGENTS.md) — mesmo conteúdo, mesma estrutura. Os
dois arquivos mudam juntos.

## 1. O que é este projeto

O SkyClimax recompila estaticamente **After Burner Climax** (PS3, `NPUB30151`)
para Windows x64 nativo. Ele é **experimental** e está atualmente bloqueado na
descriptografia do executável de varejo. Não o descreva como funcional, jogável
ou concluído.

O backend é o [ps3recomp](https://github.com/sp00nznet/ps3recomp) v0.19.0,
vendorizado em `.vendor/` (não comitado). O SkyClimax acrescenta ferramentas de
análise e, mais adiante, código de compatibilidade específico do jogo.

## 2. Arquitetura que você deve respeitar

```text
.pkg ──pkg_extract.py──▶ EBOOT.BIN ──[KEY REQUIRED]──▶ EBOOT.elf
      ──ppu_loader.py──▶ functions/image/imports JSON
      ──ppu_lifter.py──▶ ppu_recomp_*.cpp ──MSVC──▶ skyclimax.exe + ps3recomp runtime
```

Responsabilidade das camadas:

| Camada | Responsável | Regra |
|---|---|---|
| Leitores de contêiner | SkyClimax (`src/skyclimax/`) | Python puro, sem dependências de runtime de terceiros |
| Recompilador e runtime | ps3recomp (vendorizado) | nunca editar no lugar; aplicar patch em `tools/patches/` |
| Compatibilidade específica do jogo | SkyClimax (`src/hle/`) | só é adicionada quando uma importação real exigir |
| Compilação e CI | SkyClimax | CMake + scripts |

Nunca edite o C++ gerado à mão. Ele é regenerado a cada elevação.

## 3. Ferramentas fixadas

As versões ficam em `scripts/versions.env` e são registradas em
`docs/pt-BR/research/tooling.md`. Não atualize uma ferramenta sem atualizar os
dois arquivos e registrar novamente a saída de verificação.

| Ferramenta | Versão | Observação |
|---|---|---|
| Ghidra | 12.2 | exige JDK 25 (`application.java.min=25`) |
| Temurin JDK | 25.0.5+8 | o JDK 21 é rejeitado |
| Node.js | 24.22.3 | o REA 6.9.0 exige `^22.23.4 \|\| ^24.22.1 \|\| >=26.12.1` |
| Python | 3.13.x | venv em `.venv/` |
| ps3recomp | 0.19.0 | commit `ae92407bb1d899e3d32143e360fe6e6d4d8fa1b5` |

## 4. Regras invioláveis

1. **Nunca invente dados.** Nenhum nome de função, endereço, NID, estrutura ou
   comportamento que não tenha sido observado em um arquivo ou produzido por uma
   ferramenta. Se um valor é desconhecido, escreva que é desconhecido e diga o
   que o determinaria.
2. **Nunca falsifique um stub.** Um stub que retorna sucesso sem implementar
   comportamento deve se chamar `stub_<nid>_unimplemented` e registrar em log uma
   vez, na primeira chamada. Ele deve aparecer na matriz de compatibilidade como
   não implementado.
3. **Nunca afirme que um teste passou sem executá-lo.** Cole o comando e a saída
   real na mensagem de commit ou no relatório.
4. **Nunca marque um marco como validado sem evidência.** Evidência significa um
   comando mais seu resultado registrado em `docs/*/compatibility-matrix.md`.
5. **Nunca comite dados do jogo.** Nada de `.pkg`, `.rap`, `.elf`, `.self`,
   assets descriptografados, chaves ou conteúdo de `work/`. O `.gitignore` já
   cobre esses casos.
6. **Nunca modifique os arquivos originais do jogo.** Toda extração vai para
   `work/`.
7. **Nunca contorne um bloqueio documentado em silêncio.** Se você não conseguir
   descriptografar, compilar ou executar algo, diga isso e atualize o documento
   de problemas conhecidos.

## 5. Regra de documentação bilíngue

- `docs/en-US/` é o idioma-fonte; `docs/pt-BR/` é uma tradução fiel. Mesmos
  arquivos, mesma estrutura de títulos, mesmos blocos de código.
- A prosa é traduzida. Código, comandos, caminhos, identificadores, mensagens de
  log e diagnósticos de baixo nível ficam em inglês.
- Todo documento que muda deve mudar nas duas árvores **no mesmo commit**.
- Execute o portão antes de concluir:

```bash
python scripts/check_docs_parity.py
```

- Se uma tradução estiver incompleta, adicione `TODO(pt-BR)` e liste-a em
  `docs/README.md`. Nunca marque uma tradução parcial como concluída.
- A terminologia vem de `docs/pt-BR/glossary.md`. Não invente sinônimos.

## 6. Convenções de código

- Python: 3.10+, `from __future__ import annotations`, anotações de tipo em
  funções públicas, dataclasses para registros, sem importações de terceiros em
  `src/skyclimax/`.
- Todo módulo de análise documenta seu layout de bytes na docstring do módulo e
  nomeia o arquivo real que o verificou.
- Os analisadores levantam erro em entrada malformada; nunca truncam em silêncio
  nem adivinham.
- CLI: `argparse`, um subcomando por formato, `--json` para saída de máquina,
  erros em stderr com código de saída 1.
- C/C++ (gerado e HLE): C++20, `extern "C"` na fronteira, memória do convidado
  apenas por `vm_read*`/`vm_write*`.
- Comentários explicam *por quê*, não *o quê*. Nunca comente código; apague.

## 7. Regras de análise

1. Estabeleça o formato do contêiner a partir do próprio arquivo (magic,
   tamanhos, entropia), não pela extensão.
2. Valide contagens de forma cruzada: um campo de cabeçalho que declara N itens
   precisa ser conferido contra o número de itens realmente analisados.
3. Quando uma sondagem de layout falha, reporte a falha e pare. Não teste
   variantes até algo "parecer plausível".
4. Registre cada número não óbvio na documentação com o comando que o produziu.
5. Prefira `work/reports/*.json` como trilha de evidências; esses arquivos são
   ignorados pelo git, mas reproduzíveis.

## 8. Compilação e testes

```bash
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e ".[dev]"
.venv/Scripts/python.exe -m pytest
.venv/Scripts/python.exe scripts/check_docs_parity.py
```

- Os testes unitários precisam passar em um clone limpo, sem arquivos do jogo.
- Os testes de integração são ignorados automaticamente quando o pacote está
  ausente; nunca faça a suíte depender do jogo.
- A CI executa os dois portões no Windows. CI vermelha bloqueia o merge.

## 9. Método de trabalho

- Trabalhe em passos pequenos e verificáveis, com um critério de conclusão
  objetivo.
- Antes de alterar um analisador, salve a saída atual e compare depois da
  mudança.
- Antes de declarar uma construção como não suportada, verifique a documentação
  do backend e o `--help` da ferramenta.
- Atualize `docs/*/compatibility-matrix.md` sempre que uma capacidade mudar de
  estado.
- Registre novas decisões arquiteturais como um ADR em
  `docs/pt-BR/architecture/decisions.md` e no equivalente en-US; acrescente,
  nunca reescreva.

## 10. Definição de concluído

Uma tarefa está concluída quando todos os itens abaixo valem:

1. A mudança de código ou documentação está completa e consistente.
2. `pytest` passa localmente com a saída registrada.
3. `check_docs_parity.py` passa.
4. As duas árvores de idioma estão atualizadas.
5. A matriz de compatibilidade reflete o novo estado.
6. A mensagem de commit declara o que mudou e qual comando verificou.

Uma tarefa **não** está concluída porque compila, porque o código "parece certo"
ou porque a etapa anterior deu certo.
