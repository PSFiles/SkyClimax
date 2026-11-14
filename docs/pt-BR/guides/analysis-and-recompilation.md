# Guia de análise e recompilação

Procedimento ponta a ponta para ir do pacote de varejo ao C++ elevado. Cada etapa
declara se foi executada aqui.

## 1. Extrair

```bash
python .vendor/ps3recomp/tools/pkg_extract.py "$SKYCLIMAX_PKG" work/pkg
```

Validado: 46 arquivos.

## 2. Inspecionar o contêiner do executável

```bash
python -m skyclimax self-info work/pkg/USRDIR/EBOOT.BIN --json work/reports/self.json
```

Validado. Espere `retail_encrypted: true`, `entry: 0x4CDF00`, 8 cabeçalhos de
programa.

## 3. Descriptografar

Não executado e não automatizável a partir do pacote apenas.

Artefato necessário: um ELF `ET_EXEC` PPC64 big-endian. Duas fontes aceitáveis:

- uma chave do título fornecida pelo dono, usada com uma ferramenta de
  descriptografia de SELF;
- um executável despejado de uma cópia em execução do jogo.

Registre o SHA-256 do resultado. Se o cabeçalho ELF não ler `e_machine = 21` e
`e_entry = 0x4CDF00`, o arquivo errado foi descriptografado.

## 4. Carregar

```bash
python .vendor/ps3recomp/tools/ppu_loader.py work/game/EBOOT.elf -o work/meta
```

Validado em um ELF sintético; esperado na imagem real:

- `unique functions` diferente de zero (a tabela de OPD é autoritativa);
- um valor de `module TOC (r2)`;
- uma contagem de importações de firmware na casa das centenas.

Se `unique functions` for 0, a seção `.opd` não foi encontrada — a imagem
provavelmente está sem símbolos ou truncada. Pare e corrija isso antes de
elevar.

## 5. Revisar a superfície de importações

A lista de importações determina o trabalho de HLE. Agrupe por biblioteca e
verifique cada uma contra o estado dos módulos do backend. Bibliotecas sem
implementação precisam ser escritas antes que o título possa iniciar; esse é o
principal direcionador de escopo.

## 6. Elevar

```bash
python .vendor/ps3recomp/tools/ppu_lifter.py work/game/EBOOT.elf -o generated/ \
  --functions work/meta/EBOOT.functions.json \
  --imports work/meta/EBOOT.imports.json
```

Validado em um ELF sintético (1 função → 1.117 linhas). Na imagem real, espera-se
que leve minutos e emita milhares de funções em vários blocos.

Verificações de sanidade após elevar:

- a contagem de funções nas fontes geradas é igual à do carregador;
- não há linhas `WARNING: ... has no continuation` (cada uma é um intervalo de
  função mal dimensionado);
- a árvore gerada compila.

## 7. Analisar no Ghidra

```bash
export JAVA_HOME="$(pwd)/.tools/jdk25/jdk-25.0.5+8"
.tools/ghidra/ghidra_12.2_PUBLIC/support/analyzeHeadless work/ghidra_proj skyclimax \
  -import work/game/EBOOT.elf -processor "PowerPC:BE:64:default"
```

Validado com um ELF sintético (importação bem-sucedida, linguagem correta
selecionada).

Use o Ghidra para o que o liftedor não entrega: nomear funções, recuperar
estruturas e responder "para onde este ponteiro aponta". Mantenha os nomes em um
arquivo JSON e alimente-os de volta pela opção `--names` do liftedor, para que o
código gerado permaneça legível.

## 8. Tratar construções não suportadas

Quando o liftedor encontra uma instrução ou padrão que não consegue expressar:

1. Anote o endereço do convidado e o mnemônico.
2. Decida se precisa de uma mudança no liftedor (upstream) ou de um shim HLE
   (aqui).
3. Se precisar de mudança no liftedor, escreva um patch em `tools/patches/` e
   registre no log de decisões.
4. Adicione um caso de regressão em `tools/regress/` para que a construção
   permaneça coberta.

Nunca edite o C++ gerado à mão: ele é regenerado a cada elevação.

## 9. Validar uma elevação

Uma elevação está correta quando a função gerada produz o mesmo estado
arquitetural que a função do convidado. Verificações práticas, da mais barata
para a mais cara:

- o valor de retorno da função para uma entrada fixa;
- a memória do convidado que ela escreve, comparada com uma execução de
  referência;
- um traço das syscalls que ela faz, comparado com a referência.

"Compila" não é validação.

## 10. Modos de falha comuns

| Sintoma | Causa provável |
|---|---|
| a função gerada retorna imediatamente | o intervalo da função terminou cedo; procure avisos `has no continuation` |
| falha dentro de `ps3_indirect_call` | o ponteiro de função do convidado não foi resolvido como OPD |
| a chamada HLE retorna sucesso mas nada acontece | stub implementado como no-op |
| resultados de ponto flutuante errados | semântica de paired-single ou de multiplicação-adiação fundida |
| travamento em um laço | a condição do convidado depende de uma syscall não implementada |
