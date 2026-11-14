# Guia de desenvolvimento

## Preparação

Siga a [preparação do ambiente](build/environment.md). Depois:

```bash
.venv/Scripts/python.exe -m pytest
.venv/Scripts/python.exe scripts/check_docs_parity.py
```

## Estrutura

```text
src/skyclimax/       analysis library (no third-party runtime dependencies)
tests/               pytest suite; synthetic fixtures + optional real-package tests
scripts/             installers, parity checker, verification helpers
docs/en-US/          source-of-truth documentation
docs/pt-BR/          faithful translation, machine-checked
generated/           lifter output (git-ignored)
```

## Alterar um analisador

1. Reproduza o comportamento atual contra o arquivo real e salve o relatório
   JSON em `work/reports/`.
2. Altere o analisador.
3. Reexecute o mesmo comando e compare os dois relatórios.
4. Adicione ou atualize um teste de fixture sintética em `tests/conftest.py`
   para que a mudança fique coberta sem o pacote de varejo.
5. Atualize a docstring do módulo — ela é a especificação do formato.
6. Atualize as duas árvores de idioma e execute o verificador de paridade.

Nunca altere um analisador para fazer uma fixture passar. Se a fixture discorda
do arquivo real, a fixture está errada.

## Adicionar um novo formato de contêiner

1. Adicione `src/skyclimax/<formato>.py` com uma docstring de módulo contendo o
   layout de bytes e uma nota sobre qual arquivo real o verificou.
2. Adicione um auxiliar `build_<formato>()` em `tests/conftest.py`.
3. Adicione testes para o caminho feliz, um arquivo truncado e um magic errado.
4. Registre o magic em `MAGIC_PROBES` para que o `inventory` o classifique.
5. Adicione um subcomando de CLI que imprima JSON e aceite `--json`.
6. Documente em `docs/en-US/analysis/assets.md` **e** no equivalente pt-BR.

## Adicionar cobertura HLE

Somente quando uma importação real exigir:

1. Capture a chamada que falha: NID, biblioteca, endereço do chamador,
   argumentos.
2. Descubra o comportamento documentado dessa exportação.
3. Implemente em `src/hle/`, retornando os códigos de erro documentados.
4. Adicione um teste que a chame com os mesmos argumentos e verifique o retorno.
5. Registre o NID na matriz de compatibilidade.

Um stub que retorna sucesso sem implementar comportamento não é cobertura. Se
uma função precisar ser stub, nomeie-a `stub_<nid>_unimplemented` e registre em
log uma vez, na primeira chamada.

## Reproduzir um defeito

Registre quatro coisas: o comando, a entrada, o resultado esperado e o resultado
observado. Se houver uma falha, capture o endereço do convidado e a pilha do
hospedeiro separadamente — uma falha do convidado e uma falha do hospedeiro têm
causas completamente diferentes.

## Testes

| Tipo | Local | Exige o jogo |
|---|---|---|
| Unitário | `tests/test_containers.py` | não |
| Integração | `tests/test_real_package.py` | sim, ignorado automaticamente |
| Paridade de documentação | `scripts/check_docs_parity.py` | não |

A CI executa os testes unitários e o verificador de paridade no Windows. Os
testes de integração são ignorados lá porque o pacote não está no repositório.

## Regras de commit

- Uma mudança coerente por commit.
- A documentação e sua tradução entram no mesmo commit.
- Um commit que altera comportamento declara o comando usado para verificá-lo.
- Nunca comitar `work/`, `.tools/`, `.vendor/`, `.venv/` ou qualquer arquivo do
  jogo.

## Adicionar um marco

Os marcos ficam na [visão geral da arquitetura](architecture/overview.md). Um
marco só passa para `validado` quando um comando e sua saída são registrados no
log de validação da matriz de compatibilidade.
