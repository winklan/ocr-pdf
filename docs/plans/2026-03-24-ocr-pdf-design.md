# Design: Sistema OCR — Conversor de PDF Digitalizado em PDF Editável

**Data:** 2026-03-24
**Status:** Aprovado

---

## Visão Geral

Aplicação web local (sem internet) para converter PDFs digitalizados em PDFs pesquisáveis, PDFs limpos (só texto) e arquivos `.txt`, usando OCR offline com Tesseract e Poppler.

**Contexto:** Uso no TJRN para processar documentos judiciais extensos (~10.000 páginas), com fragmentação automática em lotes.

---

## Requisitos

- **Ambiente:** Aplicação web local (`http://localhost:5000`)
- **Modo:** 100% offline, sem dependências externas
- **Idioma OCR:** Português brasileiro (ç, ã, á, etc.)
- **Formatos de saída:** PDF pesquisável, PDF limpo (só texto), `.txt`
- **Escala:** Documentos grandes (~10.000 páginas), fragmentados em lotes
- **Arquivos gerados:** Salvos permanentemente em pasta `output\`

---

## Arquitetura

```
NAVEGADOR (frontend)
  index.html + app.js + style.css
  - Upload do PDF
  - Seleção de formatos de saída
  - Barra de progresso em tempo real (SSE)
  - Lista de downloads por lote
        │ HTTP (localhost:5000)
BACKEND (Flask/Python)
  app.py         → rotas Flask
  ocr_engine.py  → pipeline OCR
  /upload        → recebe o PDF
  /process       → inicia OCR em background
  /progress      → stream SSE com progresso
  /download      → entrega arquivo gerado
```

---

## Pipeline de Processamento

1. Upload do PDF
2. Validação (formato, tamanho)
3. Detecção do número de páginas via `pdfinfo` (Poppler)
4. Cálculo automático de lotes (padrão: 500 páginas/lote)
5. Confirmação pelo usuário
6. Para cada lote:
   - Poppler (`pdftoppm`, 300 DPI) → imagens PNG temporárias
   - Tesseract OCR (por página) → texto + posição
   - Geração dos arquivos de saída selecionados
   - Limpeza automática das imagens temporárias
7. Arquivos disponíveis para download imediato por lote

---

## Formatos de Saída

| Formato | Descrição |
|---|---|
| PDF pesquisável | Imagem original + texto invisível sobreposto (Ctrl+F funciona) |
| PDF limpo | Só o texto extraído, sem imagens |
| `.txt` | Texto puro, páginas separadas por marcador |

---

## Interface do Usuário

- Drag & drop ou seleção de arquivo
- Checkboxes para os 3 formatos de saída
- Campo configurável para tamanho do lote (padrão: 500)
- Exibição de: total de páginas, número de lotes
- Barra de progresso com página atual e tempo estimado
- Lista de arquivos gerados com botão de download por lote
- Botão "Cancelar" disponível durante o processamento

---

## Estrutura de Arquivos

```
C:\Users\Henrique\ocr-pdf\
├── app.py
├── ocr_engine.py
├── requirements.txt
├── start.bat
├── templates\
│   └── index.html
├── static\
│   ├── style.css
│   └── app.js
├── uploads\        # limpos após processamento
├── temp\           # imagens PNG (limpas por lote)
└── output\         # arquivos gerados (permanentes)
```

---

## Dependências

**Python (pip):**
- flask
- pytesseract
- Pillow
- fpdf2
- reportlab
- pdf2image

**Binários locais:**
- Tesseract OCR (a instalar)
- Poppler (já instalado em `C:\Users\Henrique\poppler\poppler-24.08.0\`)

---

## Estimativas de Desempenho

- Tesseract: ~10–20 páginas/minuto em hardware comum
- 500 páginas/lote ≈ 25–50 minutos por lote
- 10.000 páginas ≈ 10–20 horas no total
