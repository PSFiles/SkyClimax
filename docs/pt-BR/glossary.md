# Glossário

Terminologia bilíngue do projeto SkyClimax. A coluna en-US é o termo de origem;
use sempre a mesma tradução em todos os documentos.

| Termo (en-US) | Termo (pt-BR) | Significado |
|---|---|---|
| static recompilation | recompilação estática | Traduzir código de máquina do convidado para código-fonte do hospedeiro antecipadamente, sem interpretação de instruções em tempo de execução. |
| lifter | liftedor | O componente que traduz uma única função do convidado para código-fonte do hospedeiro. |
| lifting | elevação de código | O ato de produzir código-fonte do hospedeiro a partir de instruções do convidado. |
| guest | convidado | A plataforma emulada ou recompilada (aqui: PlayStation 3). |
| host | hospedeiro | A máquina que executa o resultado (aqui: Windows x64). |
| PPU | PPU | PowerPC Processing Unit, o núcleo principal de uso geral do Cell. |
| SPU | SPU | Synergistic Processing Unit, o coprocessador vetorial do Cell. |
| syscall | syscall | Uma chamada do código do convidado ao kernel do convidado (instrução `sc`). |
| stub | stub | Uma função do hospedeiro que substitui um ponto de entrada de biblioteca do convidado. |
| HLE | HLE | Emulação de alto nível: implementar uma biblioteca do convidado nativamente em vez de executar seu código original. |
| NID | NID | Identificador de 32 bits usado pelo PS3 para nomear uma função exportada de biblioteca. |
| PRX | PRX | Formato de módulo relocável (biblioteca compartilhada) do PS3. |
| SELF | SELF | Contêiner ELF assinado usado para executáveis de varejo. |
| EDAT | EDAT | Contêiner de dados criptografados usado para algumas cargas do jogo. |
| OPD | OPD | Official Procedure Descriptor: um par `{code, TOC}` de 8 bytes usado como ponteiro de função. |
| TOC | TOC | Ponteiro da tabela de conteúdo mantido em `r2` para a ABI de 32 bits. |
| PKG | PKG | Contêiner de pacote do PlayStation que carrega o download da loja. |
| PSARC | PSARC | Formato de arquivo da Sony usado por `rom.psarc`. |
| FARC | FARC | Formato de arquivo da Sega usado por `SYSTEM.farc` e `shader_cg.farc`. |
| ADX | ADX | Formato de fluxo de áudio da CRI Middleware. |
| Cg | Cg | Linguagem de sombreamento da NVIDIA; a versão de PS3 traz programas `.vp`/`.fp` compilados. |
| RSX | RSX | A GPU do PS3 e sua interface de comandos. |
| milestone | marco | Um ponto de verificação verificável no roteiro. |
| planned | planejado | Projetado, mas ainda não escrito. |
| implemented | implementado | Escrito e presente no repositório. |
| validated | validado | Exercitado com um comando registrado e um resultado registrado. |
| parity | paridade | Os documentos en-US e pt-BR carregam o mesmo conteúdo e a mesma estrutura. |
