# Análise do pacote

Fonte: `UP0177-NPUB30151_00-AFTERBURNERCMX00.pkg`, 551.772.592 bytes, fornecido
localmente pelo dono do projeto. Nenhum byte do pacote é armazenado no
repositório.

Reproduza com:

```bash
python -m skyclimax pkg-info UP0177-NPUB30151_00-AFTERBURNERCMX00.pkg
```

## Cabeçalho

| Campo | Valor | Observação |
|---|---|---|
| magic | `7f 50 4b 47` | `\x7fPKG` |
| revisão | `0x80000001` | pacote PS3 de varejo |
| content ID | `UP0177-NPUB30151_00-AFTERBURNERCMX00` | igual ao nome do arquivo |
| contagem de itens | 46 | igual ao número de arquivos extraídos |
| tamanho total | 551.772.592 | igual ao tamanho do arquivo em disco |
| deslocamento de dados | 384 | |
| tamanho dos dados | 551.772.112 | |

O par `info_offset`/`info_size` em `0x08`/`0x0C` lê `192`/`8`, o que não
concorda com `item_count × 8 = 368` para uma tabela plana de
`{u32 id, u32 size}`. Essa discrepância é registrada como não resolvida em vez
de ser explicada artificialmente; a enumeração de entradas é delegada ao
extrator testado do ps3recomp, cuja contagem de arquivos valida `item_count` de
forma cruzada.

## Árvore extraída

| Caminho | Bytes | Tipo |
|---|---|---|
| `PARAM.SFO` | 1.040 | metadados do sistema |
| `PS3LOGO.DAT` | 5.120 | logo de inicialização |
| `ICON0.PNG` | 59.468 | ícone |
| `ICON1.PAM` | 1.974.272 | ícone animado |
| `PIC0.PNG` | 204.415 | plano de fundo |
| `PIC1.PNG` | 1.929.465 | plano de fundo |
| `USRDIR/EBOOT.BIN` | 5.656.176 | SELF criptografado |
| `USRDIR/chkboot.edat` | 25.712 | carga EDAT |
| `USRDIR/lang/en/string_array.bin` | 26.944 | localização |
| `USRDIR/ps3/SYSTEM.farc` | 791.247 | Sega FArc |
| `USRDIR/ps3/rom.psarc` | 407.077.221 | PSARC, 96 % da carga |
| `USRDIR/ps3/shader_cg.farc` | 200.315 | arquivo de shaders Cg |
| `USRDIR/rom/adx/*.adx` | 20 arquivos | música CRI ADX |
| `USRDIR/rom/adx/voice.afs` | 38.895.616 | arquivo de vozes CRI AFS |
| `USRDIR/string_array.bin` | 35.472 | localização |
| `TROPDIR/NPWR00981_00/TROPHY.TRP` | 671.472 | troféus |

## Metadados do sistema

`PARAM.SFO` decodifica para:

| Chave | Valor |
|---|---|
| `TITLE` | `After Burner Climax` |
| `TITLE_ID` | `NPUB30151` |
| `CATEGORY` | `HG` (instalado no HDD) |
| `VERSION` | `01.00` |
| `APP_VER` | `01.00` |
| `PS3_SYSTEM_VER` | `03.0000` |
| `PARENTAL_LEVEL` | `4` |
| `BOOTABLE` | `1` |

`PS3_SYSTEM_VER 03.0000` significa que o título tem como alvo o firmware 3.00,
ou seja, a superfície de syscalls anterior à 3.41. Isso importa depois: a camada
HLE precisa cobrir as exportações de `sysPrxForUser` da era 3.00, não as de um
firmware moderno.

## Reproduza a extração

```bash
python .vendor/ps3recomp/tools/pkg_extract.py UP0177-NPUB30151_00-AFTERBURNERCMX00.pkg work/pkg
```

O extrator descriptografa com a chave AES-CTR pública `PS3_GPKG` e não precisa de
arquivo RAP por título. O `.rap` fornecido junto ao pacote tem 16 bytes — um
klicensee bruto — e **não** é necessário para esta etapa. Ele só é relevante
para cargas EDAT, como `chkboot.edat`.
