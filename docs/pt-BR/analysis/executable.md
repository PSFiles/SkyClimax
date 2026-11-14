# Análise do executável

Fonte: `USRDIR/EBOOT.BIN`, 5.656.176 bytes, extraído do pacote de varejo.
Reproduza com:

```bash
python -m skyclimax self-info work/pkg/USRDIR/EBOOT.BIN
```

## Contêiner

| Campo | Valor |
|---|---|
| magic | `SCE\0` |
| versão do SELF | 2 |
| revisão de chave | 1 (varejo, assinado e criptografado) |
| tipo de cabeçalho | 1 |
| tamanho dos metadados | 1.184 |
| extensão do cabeçalho | 2.688 (`0xA80`) |
| tamanho do ELF contido | 5.653.432 (`0x5643B8`) |
| cabeçalhos de programa | 8 |
| cabeçalhos de seção | 31 |

## Cabeçalho ELF embutido

O cabeçalho ELF é copiado para o cabeçalho do SELF e, portanto, é legível mesmo
que os segmentos não sejam:

| Campo | Valor | Significado |
|---|---|---|
| classe | 2 | ELF64 |
| dados | 2 | big-endian |
| OSABI | `0x66` | PlayStation 3 |
| `e_type` | 2 | `ET_EXEC` — endereço de carga fixo, sem relocações |
| `e_machine` | 21 | `EM_PPC64` |
| `e_entry` | `0x4CDF00` | descritor OPD, não código |
| `e_phoff` | `0x40` | |
| `e_flags` | 0 | |

`ET_EXEC` é o caso fácil para recompilação estática: a imagem carrega em um
endereço fixo, então nenhum processamento de relocação é necessário para o
executável principal.

## Cabeçalhos de programa

| # | tipo | perms | vaddr | filesz | memsz | bss |
|---|---|---|---|---|---|---|
| 0 | `PT_LOAD` | R+X | `0x10000` | `0x4A7060` | `0x4A7060` | 0 |
| 1 | `PT_LOAD` | R+W | `0x4C0000` | `0xB1B14` | `0x12554A8` | `0x11A3994` |
| 2 | `PT_LOAD` | R | 0 | 0 | 0 | 0 |
| 3 | `PT_LOAD` | R+W | 0 | 0 | 0 | 0 |
| 4 | `PT_LOAD` | R+W | 0 | 0 | 0 | 0 |
| 5 | `PT_TLS` | R | `0x4EF27C` | 4 | `0x1EC` | `0x1E8` |
| 6 | `0x60000001` | – | `0x4B7000` | `0x20` | `0x20` | 0 |
| 7 | `0x60000002` | – | `0x4B7020` | `0x40` | `0x40` | 0 |

Três observações que orientam a arquitetura:

1. **O ponto de entrada fica no segmento de dados.** `0x4CDF00` cai dentro do
   cabeçalho de programa 1 (`0x4C0000`–`0x4E554A8`), que é `R+W` e não
   executável. Esse é o layout clássico de OPD: a entrada é um descritor de
   8 bytes `{code, TOC}`, então o carregador precisa resolvê-lo antes de
   executar. O carregador do ps3recomp faz exatamente isso e reporta
   `entry (OPD) -> code, toc`.
2. **O BSS tem 17,3 MB** (`0x11A3994`) contra 727 KB de dados inicializados.
   Qualquer implementação no hospedeiro precisa reservar o `memsz` completo, não
   apenas o `filesz`.
3. **O cabeçalho de programa 7 é o segmento de parâmetros do PS3**
   (`p_type 0x60000002`), onde fica a tabela de importações de firmware. Em uma
   imagem descriptografada, essa é a fonte autoritativa de triplas
   `(biblioteca, NID, endereço do stub)`.

## Estado da criptografia

Todos os segmentos de carga estão criptografados com AES. Evidência: os
primeiros 64 KiB do segmento 0 têm entropia de **7,9973 bits/byte**, e nenhum
fluxo de instruções legível ou tabela de strings aparece em qualquer ponto dos
dados do segmento. O texto claro termina na fronteira dos metadados do SELF
(`0xA80`).

Consequências, ditas com clareza:

- **Nenhuma contagem de funções, lista de importações ou nome de símbolo pode
  ser reportada.** Qualquer coisa desse tipo neste repositório seria fabricada.
- A descoberta de funções guiada por `.opd`, da qual os projetos de referência
  dependem, não pode rodar até que a imagem seja descriptografada.
- O Ghidra não consegue analisar o arquivo como está; ele importaria 5,6 MB de
  ruído.

## O que desbloqueia isso

Em ordem decrescente de preferência:

1. **Chaves fornecidas pelo usuário.** Um arquivo `keys` para descriptografia no
   estilo `scetool`, ou o klicensee mais a chave de aplicação do título. O `.rap`
   de 16 bytes ao lado do pacote é um klicensee para cargas EDAT e não é
   suficiente, sozinho, para o SELF.
2. **Um dump descriptografado produzido pelo dono.** O RPCS3 consegue despejar
   um executável descriptografado ao carregar o título; o ELF resultante é
   idêntico byte a byte às imagens `PT_LOAD` e é o que o ps3recomp espera.
3. **Extração dinâmica.** Executar o título sob um emulador com dumps de memória
   produz a mesma imagem, ao custo de um procedimento muito mais longo.

O SkyClimax não tenta burlar a proteção e não embute chaves. A imagem
descriptografada é um artefato local e está no `.gitignore`.

## Verificação cruzada com o carregador

`ppu_loader.py` é a implementação de referência dessa análise. Executado sobre
um ELF de PS3 sintético, ele reporta:

```text
e_type           : 2 (EXEC)
entry (OPD)      : 0x20000 -> code 0x10000, toc 0x20d00
load segments    : 2
```

Essa é a mesma forma do executável real, e é por isso que o teste de fumaça no
[guia de compilação](../build/build.md) é um ensaio significativo, não um
brinquedo.
