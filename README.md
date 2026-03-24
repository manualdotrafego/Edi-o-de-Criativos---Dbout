# Edição de Criativos - Dbout

Pipeline automatizado de geração de vídeos criativos para anúncios dentais, desenvolvido com Claude Code.

## O que faz

Combina automaticamente:
- **Template de vídeo base** (loop via FFmpeg)
- **Narração em áudio** gerada pela API ElevenLabs (voz Brittney, PT-BR)
- **Overlay com nome da cidade** (PIL: texto rosa, contorno branco, retângulo arredondado com sombra)
- **Legendas word-by-word** (formato ASS: Impact branco com contorno preto grosso)

## Estrutura

```
pipeline_principal.py   → Script principal configurável
scripts/
  gen_votuporanga.py
  render_batch_5cities.py
  render_dois_irmaos.py
  render_3cidades.py
  praia_grande_jan26.py
  ponta_grossa_v2_all.py
  ponta_grossa_15mar_v2.py
```

## Requisitos

```bash
# FFmpeg (com suporte a libass para legendas)
brew install ffmpeg-full

# Python
pip install pillow requests
```

## Configuração

Edite as variáveis no topo de `pipeline_principal.py`:

| Variável | Descrição |
|----------|-----------|
| `CITIES` | Lista de cidades `(label, slug, nome_narração)` |
| `TEMPLATES` | Templates a usar `(arquivo, slug, reduzir_vol)` |
| `NARRATION_TEMPLATE` | Texto da narração com `{city}` como placeholder |
| `ZIP_OUTPUT` | Caminho do ZIP de saída |

## Templates disponíveis

| Arquivo | Duração | Resolução | Obs |
|---------|---------|-----------|-----|
| `[3 MAR] .mp4` | 14s | 1080×1920 | |
| `[2 - FEV] .mp4` | 10s | 1080×1920 | |
| `14 - MAR.MOV` | 18s | 1080×1920 | |
| `15 - MAR.MOV` | 34s | 1080×1920 | |
| `16 - MAR.MOV` | 21s | 1080×1920 | |
| `17 - MAR.MOV` | 22s | 1080×1920 | |
| `18 - MAR.MOV` | 21s | 1080×1920 | |
| `19 - MAR.MOV` | 20s | 1080×1920 | |
| `20-mar.MOV` | 18s | 1080×1920 | vol -70% |
| `21-mar.MOV` | 22s | 1080×1920 | |
| `22-mar.MOV` | 17s | 1080×1920 | vol -70% |
| `24-mar.MOV` | 18s | 1080×1920 | vol -70% |
| `01 jan26.mp4` | 14s | 720×1280 | |
| `02 jan26.mp4` | 14s | 720×1280 | |
| `03 jan26.mp4` | 14s | 720×1280 | |
| `04 jan26.mp4` | 14s | 720×1280 | |

> Templates 20–24mar têm o áudio original reduzido em 70% automaticamente.

## Uso

```bash
python pipeline_principal.py
```

O ZIP com todos os vídeos será salvo no caminho definido em `ZIP_OUTPUT`.

---
Desenvolvido com [Claude Code](https://claude.ai/code)
