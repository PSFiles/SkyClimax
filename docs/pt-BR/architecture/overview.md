# Arquitetura

## Forma do sistema

O SkyClimax é uma camada fina e específica do jogo sobre o backend ps3recomp.
Ele não reimplementa um recompilador; ele configura um e acrescenta a análise e
o código de compatibilidade de que After Burner Climax especificamente precisa.

```text
  retail .pkg
      │  pkg_extract.py (public PS3_GPKG key)
      ▼
  EBOOT.BIN (SELF, encrypted)
      │  [BLOCKED: app key / decrypted dump]
      ▼
  EBOOT.elf (PPC64 BE, ET_EXEC, entry 0x4CDF00)
      │  ppu_loader.py   → image + OPD function table + NID imports
      │  ppu_disasm.py   → PPC64 listing
      │  ppu_lifter.py   → ppu_recomp_*.cpp  (one C++ function per guest function)
      ▼
  generated C++
      │  MSVC / clang-cl + CMake + Ninja   [BLOCKED: no compiler on this host]
      ▼
  skyclimax.exe  ──links──▶  ps3recomp runtime (HLE modules, RSX, SPU)
      │
      ├── cellGcmSys / RSX  → D3D12 backend
      ├── cellAudio / ADX   → host audio
      ├── cellPad           → XInput
      └── cellFs / cellSysutil / sysPrxForUser
```

## Camadas e responsabilidade

| Camada | Responsável | Conteúdo |
|---|---|---|
| Leitores de contêiner | SkyClimax | `src/skyclimax/*.py` — cabeçalho PKG, cabeçalho SELF, PARAM.SFO, FArc, ADX, PSARC, inventário |
| Recompilador | ps3recomp (vendorizado) | carregador, desmontador, liftedor, gerador de stubs |
| Runtime | ps3recomp (vendorizado) | `lib/ps3recomp_runtime.lib`, módulos HLE, tradução de RSX |
| Compatibilidade específica do jogo | SkyClimax | substituições de stub e configuração por título, adicionadas apenas quando a evidência exige |
| Compilação | SkyClimax | cola de CMake, scripts, CI |

A fronteira é deliberada: o SkyClimax nunca modifica as ferramentas vendorizadas.
Se uma mudança no backend for necessária, ela é expressa como um arquivo de
patch em `tools/patches/`, para que a versão vendorizada permaneça fixa e
auditável.

## Contrato de fluxo de dados

Cada etapa consome e produz arquivos, nunca estado em memória:

| Etapa | Entrada | Saída |
|---|---|---|
| extrair | `.pkg` | `work/pkg/**` |
| inspecionar | `EBOOT.BIN` | `work/reports/self.json` |
| carregar | `EBOOT.elf` | `*.functions.json`, `*.image.json`, `*.imports.json` |
| elevar | ELF + tabela de funções | `ppu_recomp_*.cpp`, `ppu_recomp.h` |
| compilar | C++ gerado + runtime | `skyclimax.exe` |

Isso torna cada etapa individualmente reproduzível e individualmente testável,
que é a única forma de o projeto continuar depurável quando uma elevação de
14.000 funções produz um pixel errado três etapas depois.

## Interfaces entre convidado e hospedeiro

Três interfaces concentram quase todo o risco:

1. **Memória do convidado.** O código recompilado desreferencia endereços do
   convidado. O runtime fornece acessores big-endian `vm_read*`/`vm_write*`
   sobre uma região reservada; o hospedeiro nunca deve entregar um ponteiro
   bruto do convidado a código do hospedeiro.
2. **Chamadas indiretas.** Um ponteiro de função do convidado é um endereço de
   OPD, não de código. O despacho resolve OPD → código antes de chamar a função
   do hospedeiro registrada.
3. **Syscalls.** `sc` vira uma chamada ao despachante HLE. O que não estiver
   implementado deve falhar ruidosamente com o número da syscall e o endereço do
   chamador, nunca retornar zero em silêncio.

## Por que esta forma e não outra

- **Não um liftedor do zero.** Escrever um liftedor de PPC64 que trate VMX128,
  floats emparelhados e a ABI de 32 bits corretamente é um projeto de vários
  meses por si só, e nove projetos de referência já dependem de uma
  implementação. Duplicá-la adicionaria risco sem adicionar capacidade.
- **Não um emulador.** O objetivo é execução nativa; um interpretador no meio do
  caminho contradiz a premissa.
- **Não um renderizador por jogo.** A tradução Cg/RSX é infraestrutura
  compartilhada; mantê-la fora do código do jogo é o que torna o próximo título
  mais barato.

## Posição atual no pipeline

| Marco | Estado |
|---|---|
| M0 toolchain instalada e validada | validado |
| M1 pacote aberto, inventário reproduzível | validado |
| M2 contêiner do executável analisado | validado |
| M3 pipeline de elevação provado em um ELF sintético | validado |
| M4 compilação nativa do código elevado | planejado — bloqueado, sem compilador e sem fontes do runtime |
| M5 EBOOT descriptografado elevado | validado — 15.237 funções |
| M6 inicialização do runtime e primeiro quadro | planejado |
| M7 jogável | planejado |

O projeto é **experimental**. O último marco efetivamente alcançado é o M5: a
imagem está elevada, mas nada foi compilado nem executado.
