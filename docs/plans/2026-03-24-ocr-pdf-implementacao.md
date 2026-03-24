# OCR PDF — Plano de Implementação

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Construir uma aplicação web local (Flask) que converte PDFs digitalizados em PDF pesquisável, PDF limpo e .txt usando Tesseract OCR + Poppler, com suporte a fragmentação para documentos grandes (~10.000 páginas).

**Architecture:** Servidor Flask em localhost:5000 expõe rotas de upload, processamento em background e streaming de progresso via SSE. O motor OCR usa pdf2image (wrapper do Poppler já instalado) para converter páginas em imagens e pytesseract para extrair texto. A interface HTML/JS faz upload, exibe progresso em tempo real e lista arquivos para download.

**Tech Stack:** Python 3, Flask, pytesseract, pdf2image, Pillow, pypdf, fpdf2, SSE (Server-Sent Events), HTML/CSS/JS vanilla

---

## Pré-requisitos (fazer antes de começar)

### Instalar Tesseract OCR para Windows

1. Baixar instalador: https://github.com/UB-Mannheim/tesseract/wiki
   - Escolher `tesseract-ocr-w64-setup-5.x.x.exe`
   - Durante a instalação, marcar **"Additional language data → Portuguese"**
2. Caminho padrão após instalação: `C:\Program Files\Tesseract-OCR\tesseract.exe`
3. Verificar no terminal:
   ```
   "C:\Program Files\Tesseract-OCR\tesseract.exe" --version
   ```
   Esperado: `tesseract 5.x.x`

### Instalar Python e dependências

```bash
cd C:\Users\Henrique\ocr-pdf
python -m venv venv
venv\Scripts\activate
pip install flask pytesseract Pillow pdf2image pypdf fpdf2
```

---

## Task 1: Estrutura inicial do projeto

**Files:**
- Create: `C:\Users\Henrique\ocr-pdf\app.py`
- Create: `C:\Users\Henrique\ocr-pdf\ocr_engine.py`
- Create: `C:\Users\Henrique\ocr-pdf\requirements.txt`
- Create: `C:\Users\Henrique\ocr-pdf\templates\index.html`
- Create: `C:\Users\Henrique\ocr-pdf\static\style.css`
- Create: `C:\Users\Henrique\ocr-pdf\static\app.js`

**Step 1: Criar pastas**

```bash
cd C:\Users\Henrique\ocr-pdf
mkdir templates static uploads temp output
```

**Step 2: Criar requirements.txt**

```
flask
pytesseract
Pillow
pdf2image
pypdf
fpdf2
```

**Step 3: Criar app.py com esqueleto Flask**

```python
import os
from flask import Flask, render_template

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['TEMP_FOLDER'] = 'temp'
app.config['OUTPUT_FOLDER'] = 'output'
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024 * 1024  # 2GB

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
```

**Step 4: Criar ocr_engine.py vazio**

```python
# Motor OCR — será preenchido nas tasks seguintes
```

**Step 5: Criar index.html mínimo**

```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>OCR - Conversor de PDF</title>
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>
    <h1>OCR - Conversor de PDF Digitalizado</h1>
    <script src="/static/app.js"></script>
</body>
</html>
```

**Step 6: Verificar que o servidor sobe**

```bash
cd C:\Users\Henrique\ocr-pdf
venv\Scripts\activate
python app.py
```

Abrir `http://localhost:5000` no navegador. Esperado: página com o título "OCR - Conversor de PDF Digitalizado".

**Step 7: Commit**

```bash
git init
git add .
git commit -m "feat: estrutura inicial do projeto OCR"
```

---

## Task 2: Configuração do motor OCR (caminhos e validação)

**Files:**
- Modify: `C:\Users\Henrique\ocr-pdf\ocr_engine.py`
- Create: `C:\Users\Henrique\ocr-pdf\tests\test_ocr_engine.py`

**Step 1: Escrever testes de configuração**

```python
# tests/test_ocr_engine.py
import pytest
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ocr_engine import validar_configuracao, obter_info_pdf

def test_validar_configuracao_retorna_dict():
    resultado = validar_configuracao()
    assert isinstance(resultado, dict)
    assert 'tesseract_ok' in resultado
    assert 'poppler_ok' in resultado

def test_validar_configuracao_tesseract_encontrado():
    resultado = validar_configuracao()
    assert resultado['tesseract_ok'] == True, f"Tesseract não encontrado: {resultado.get('tesseract_erro')}"

def test_validar_configuracao_poppler_encontrado():
    resultado = validar_configuracao()
    assert resultado['poppler_ok'] == True, f"Poppler não encontrado: {resultado.get('poppler_erro')}"
```

**Step 2: Rodar testes para confirmar que falham**

```bash
cd C:\Users\Henrique\ocr-pdf
venv\Scripts\activate
python -m pytest tests/test_ocr_engine.py -v
```

Esperado: `ImportError` ou `FAILED` — funções ainda não existem.

**Step 3: Implementar em ocr_engine.py**

```python
import os
import pytesseract
from pdf2image import pdfinfo_from_path

# Caminhos das ferramentas
TESSERACT_PATH = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
POPPLER_PATH = r'C:\Users\Henrique\poppler\poppler-24.08.0\Library\bin'

pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


def validar_configuracao():
    resultado = {'tesseract_ok': False, 'poppler_ok': False}

    # Verificar Tesseract
    try:
        pytesseract.get_tesseract_version()
        resultado['tesseract_ok'] = True
    except Exception as e:
        resultado['tesseract_erro'] = str(e)

    # Verificar Poppler
    try:
        poppler_exe = os.path.join(POPPLER_PATH, 'pdfinfo.exe')
        if os.path.exists(poppler_exe):
            resultado['poppler_ok'] = True
        else:
            resultado['poppler_erro'] = f'pdfinfo.exe não encontrado em {POPPLER_PATH}'
    except Exception as e:
        resultado['poppler_erro'] = str(e)

    return resultado


def obter_info_pdf(caminho_pdf):
    """Retorna dict com 'paginas' e 'nome'."""
    info = pdfinfo_from_path(caminho_pdf, poppler_path=POPPLER_PATH)
    return {
        'paginas': info['Pages'],
        'nome': os.path.basename(caminho_pdf)
    }
```

**Step 4: Rodar testes**

```bash
python -m pytest tests/test_ocr_engine.py -v
```

Esperado: 3 testes PASSED.

**Step 5: Commit**

```bash
git add ocr_engine.py tests/
git commit -m "feat: configuração do motor OCR com validação de Tesseract e Poppler"
```

---

## Task 3: Lógica de fragmentação em lotes

**Files:**
- Modify: `C:\Users\Henrique\ocr-pdf\ocr_engine.py`
- Modify: `C:\Users\Henrique\ocr-pdf\tests\test_ocr_engine.py`

**Step 1: Escrever testes**

```python
# Adicionar em tests/test_ocr_engine.py
from ocr_engine import calcular_lotes

def test_calcular_lotes_sem_fragmentacao():
    lotes = calcular_lotes(total_paginas=100, tamanho_lote=500)
    assert lotes == [(1, 100)]

def test_calcular_lotes_exato():
    lotes = calcular_lotes(total_paginas=1000, tamanho_lote=500)
    assert lotes == [(1, 500), (501, 1000)]

def test_calcular_lotes_resto():
    lotes = calcular_lotes(total_paginas=750, tamanho_lote=500)
    assert lotes == [(1, 500), (501, 750)]

def test_calcular_lotes_grande():
    lotes = calcular_lotes(total_paginas=10000, tamanho_lote=500)
    assert len(lotes) == 20
    assert lotes[0] == (1, 500)
    assert lotes[-1] == (9501, 10000)
```

**Step 2: Rodar testes para confirmar falha**

```bash
python -m pytest tests/test_ocr_engine.py::test_calcular_lotes_sem_fragmentacao -v
```

Esperado: FAILED — `ImportError`.

**Step 3: Implementar calcular_lotes**

```python
# Adicionar em ocr_engine.py
def calcular_lotes(total_paginas, tamanho_lote=500):
    """Retorna lista de tuplas (pagina_inicio, pagina_fim)."""
    lotes = []
    inicio = 1
    while inicio <= total_paginas:
        fim = min(inicio + tamanho_lote - 1, total_paginas)
        lotes.append((inicio, fim))
        inicio = fim + 1
    return lotes
```

**Step 4: Rodar todos os testes**

```bash
python -m pytest tests/test_ocr_engine.py -v
```

Esperado: todos PASSED.

**Step 5: Commit**

```bash
git add ocr_engine.py tests/test_ocr_engine.py
git commit -m "feat: lógica de fragmentação em lotes"
```

---

## Task 4: Conversão de PDF em imagens (Poppler)

**Files:**
- Modify: `C:\Users\Henrique\ocr-pdf\ocr_engine.py`

**Step 1: Escrever teste (requer PDF de teste)**

Criar um PDF de teste mínimo em `tests/fixtures/teste.pdf` (pode ser qualquer PDF de 2 páginas).

```python
# Adicionar em tests/test_ocr_engine.py
from ocr_engine import converter_paginas_em_imagens
import os

FIXTURE_PDF = os.path.join(os.path.dirname(__file__), 'fixtures', 'teste.pdf')

def test_converter_paginas_retorna_lista_de_imagens():
    if not os.path.exists(FIXTURE_PDF):
        pytest.skip("PDF de teste não encontrado")
    imagens = converter_paginas_em_imagens(FIXTURE_PDF, pagina_inicio=1, pagina_fim=1)
    assert len(imagens) == 1
    assert hasattr(imagens[0], 'size')  # é objeto PIL.Image
```

**Step 2: Implementar converter_paginas_em_imagens**

```python
# Adicionar em ocr_engine.py
from pdf2image import convert_from_path

def converter_paginas_em_imagens(caminho_pdf, pagina_inicio, pagina_fim, dpi=300):
    """
    Converte páginas de um PDF em lista de objetos PIL.Image.
    pagina_inicio e pagina_fim são 1-indexados.
    """
    imagens = convert_from_path(
        caminho_pdf,
        dpi=dpi,
        first_page=pagina_inicio,
        last_page=pagina_fim,
        poppler_path=POPPLER_PATH
    )
    return imagens
```

**Step 3: Rodar testes**

```bash
python -m pytest tests/test_ocr_engine.py -v
```

Esperado: todos PASSED (teste de imagens é pulado se não houver fixture).

**Step 4: Commit**

```bash
git add ocr_engine.py tests/
git commit -m "feat: conversão de PDF em imagens com Poppler"
```

---

## Task 5: OCR por página com Tesseract

**Files:**
- Modify: `C:\Users\Henrique\ocr-pdf\ocr_engine.py`

**Step 1: Escrever teste**

```python
# Adicionar em tests/test_ocr_engine.py
from ocr_engine import extrair_texto_imagem, extrair_pdf_pesquisavel_imagem
from PIL import Image, ImageDraw, ImageFont

def criar_imagem_com_texto(texto):
    """Cria imagem PIL simples com texto para teste."""
    img = Image.new('RGB', (400, 100), color='white')
    draw = ImageDraw.Draw(img)
    draw.text((10, 10), texto, fill='black')
    return img

def test_extrair_texto_retorna_string():
    img = criar_imagem_com_texto("Teste OCR")
    texto = extrair_texto_imagem(img)
    assert isinstance(texto, str)

def test_extrair_pdf_pesquisavel_retorna_bytes():
    img = criar_imagem_com_texto("Teste OCR")
    pdf_bytes = extrair_pdf_pesquisavel_imagem(img)
    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes[:4] == b'%PDF'  # assinatura PDF
```

**Step 2: Rodar para confirmar falha**

```bash
python -m pytest tests/test_ocr_engine.py::test_extrair_texto_retorna_string -v
```

Esperado: FAILED.

**Step 3: Implementar**

```python
# Adicionar em ocr_engine.py

def extrair_texto_imagem(imagem):
    """Extrai texto de uma imagem PIL usando Tesseract. Retorna string."""
    texto = pytesseract.image_to_string(imagem, lang='por')
    return texto

def extrair_pdf_pesquisavel_imagem(imagem):
    """
    Retorna bytes de um PDF de uma página com imagem original
    e texto invisível sobreposto (PDF pesquisável).
    """
    pdf_bytes = pytesseract.image_to_pdf_or_hocr(imagem, lang='por', extension='pdf')
    return pdf_bytes
```

**Step 4: Rodar testes**

```bash
python -m pytest tests/test_ocr_engine.py -v
```

Esperado: todos PASSED.

**Step 5: Commit**

```bash
git add ocr_engine.py tests/test_ocr_engine.py
git commit -m "feat: extração de texto e PDF pesquisável com Tesseract"
```

---

## Task 6: Geração dos arquivos de saída

**Files:**
- Modify: `C:\Users\Henrique\ocr-pdf\ocr_engine.py`

**Step 1: Escrever testes**

```python
# Adicionar em tests/test_ocr_engine.py
from ocr_engine import gerar_txt, gerar_pdf_limpo, gerar_pdf_pesquisavel
import os, tempfile

TEXTOS_TESTE = ["Texto da página 1.\n", "Texto da página 2.\n"]

def test_gerar_txt_cria_arquivo():
    with tempfile.TemporaryDirectory() as tmpdir:
        caminho = os.path.join(tmpdir, 'saida.txt')
        gerar_txt(TEXTOS_TESTE, caminho)
        assert os.path.exists(caminho)
        conteudo = open(caminho, encoding='utf-8').read()
        assert 'Texto da página 1' in conteudo
        assert '--- Página 2 ---' in conteudo

def test_gerar_pdf_limpo_cria_arquivo():
    with tempfile.TemporaryDirectory() as tmpdir:
        caminho = os.path.join(tmpdir, 'saida.pdf')
        gerar_pdf_limpo(TEXTOS_TESTE, caminho)
        assert os.path.exists(caminho)
        assert os.path.getsize(caminho) > 0
```

**Step 2: Implementar gerar_txt, gerar_pdf_limpo, gerar_pdf_pesquisavel**

```python
# Adicionar em ocr_engine.py
from fpdf import FPDF
from pypdf import PdfWriter
import io

def gerar_txt(textos_por_pagina, caminho_saida):
    """
    textos_por_pagina: lista de strings, uma por página.
    Salva arquivo .txt com marcadores de página.
    """
    with open(caminho_saida, 'w', encoding='utf-8') as f:
        for i, texto in enumerate(textos_por_pagina, start=1):
            if i > 1:
                f.write(f'\n--- Página {i} ---\n\n')
            f.write(texto)


def gerar_pdf_limpo(textos_por_pagina, caminho_saida):
    """Gera PDF contendo apenas o texto extraído, sem imagens."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font('Helvetica', size=11)

    for i, texto in enumerate(textos_por_pagina, start=1):
        if i > 1:
            pdf.add_page()
        # Limpar caracteres problemáticos para FPDF
        texto_limpo = texto.encode('latin-1', errors='replace').decode('latin-1')
        pdf.multi_cell(0, 6, texto_limpo)

    pdf.output(caminho_saida)


def gerar_pdf_pesquisavel(pdfs_por_pagina_bytes, caminho_saida):
    """
    pdfs_por_pagina_bytes: lista de bytes, um PDF de 1 página por item
                           (saída de extrair_pdf_pesquisavel_imagem).
    Mescla todas as páginas em um único PDF pesquisável.
    """
    writer = PdfWriter()
    for pdf_bytes in pdfs_por_pagina_bytes:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(pdf_bytes))
        for page in reader.pages:
            writer.add_page(page)
    with open(caminho_saida, 'wb') as f:
        writer.write(f)
```

**Step 3: Rodar testes**

```bash
python -m pytest tests/test_ocr_engine.py -v
```

Esperado: todos PASSED.

**Step 4: Commit**

```bash
git add ocr_engine.py tests/test_ocr_engine.py
git commit -m "feat: geração de arquivos txt, PDF limpo e PDF pesquisável"
```

---

## Task 7: Função principal de processamento de lote

**Files:**
- Modify: `C:\Users\Henrique\ocr-pdf\ocr_engine.py`

**Step 1: Implementar processar_lote**

```python
# Adicionar em ocr_engine.py

def processar_lote(caminho_pdf, numero_lote, pagina_inicio, pagina_fim,
                   pasta_saida, formatos, callback_progresso=None):
    """
    Processa um lote de páginas e gera os arquivos de saída.

    formatos: dict com chaves 'pesquisavel', 'limpo', 'txt' (bool)
    callback_progresso: função(pagina_atual, total_paginas) chamada a cada página

    Retorna dict com caminhos dos arquivos gerados.
    """
    total_paginas_lote = pagina_fim - pagina_inicio + 1
    textos = []
    pdfs_pesquisavel = []

    imagens = converter_paginas_em_imagens(caminho_pdf, pagina_inicio, pagina_fim)

    for i, imagem in enumerate(imagens):
        if formatos.get('txt') or formatos.get('limpo'):
            texto = extrair_texto_imagem(imagem)
            textos.append(texto)

        if formatos.get('pesquisavel'):
            pdf_bytes = extrair_pdf_pesquisavel_imagem(imagem)
            pdfs_pesquisavel.append(pdf_bytes)

        if callback_progresso:
            callback_progresso(i + 1, total_paginas_lote)

    prefixo = f'lote-{numero_lote:02d}'
    arquivos_gerados = {}

    if formatos.get('txt'):
        caminho = os.path.join(pasta_saida, f'{prefixo}.txt')
        gerar_txt(textos, caminho)
        arquivos_gerados['txt'] = caminho

    if formatos.get('limpo'):
        caminho = os.path.join(pasta_saida, f'{prefixo}-limpo.pdf')
        gerar_pdf_limpo(textos, caminho)
        arquivos_gerados['limpo'] = caminho

    if formatos.get('pesquisavel'):
        caminho = os.path.join(pasta_saida, f'{prefixo}-pesquisavel.pdf')
        gerar_pdf_pesquisavel(pdfs_pesquisavel, caminho)
        arquivos_gerados['pesquisavel'] = caminho

    return arquivos_gerados
```

**Step 2: Commit**

```bash
git add ocr_engine.py
git commit -m "feat: função principal de processamento de lote"
```

---

## Task 8: Rotas Flask — upload e informações do PDF

**Files:**
- Modify: `C:\Users\Henrique\ocr-pdf\app.py`

**Step 1: Implementar rota /upload**

```python
# app.py completo (substituir conteúdo)
import os
import uuid
from flask import Flask, render_template, request, jsonify, send_file
from ocr_engine import validar_configuracao, obter_info_pdf, calcular_lotes

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['TEMP_FOLDER'] = 'temp'
app.config['OUTPUT_FOLDER'] = 'output'
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024 * 1024  # 2GB

for pasta in ['uploads', 'temp', 'output']:
    os.makedirs(pasta, exist_ok=True)


@app.route('/')
def index():
    config = validar_configuracao()
    return render_template('index.html', config=config)


@app.route('/upload', methods=['POST'])
def upload():
    if 'arquivo' not in request.files:
        return jsonify({'erro': 'Nenhum arquivo enviado'}), 400

    arquivo = request.files['arquivo']
    if not arquivo.filename.lower().endswith('.pdf'):
        return jsonify({'erro': 'Apenas arquivos PDF são aceitos'}), 400

    session_id = str(uuid.uuid4())
    nome_arquivo = f'{session_id}.pdf'
    caminho = os.path.join(app.config['UPLOAD_FOLDER'], nome_arquivo)
    arquivo.save(caminho)

    try:
        info = obter_info_pdf(caminho)
        tamanho_lote = int(request.form.get('tamanho_lote', 500))
        lotes = calcular_lotes(info['paginas'], tamanho_lote)
        return jsonify({
            'session_id': session_id,
            'paginas': info['paginas'],
            'total_lotes': len(lotes),
            'lotes': [{'numero': i+1, 'inicio': l[0], 'fim': l[1]} for i, l in enumerate(lotes)]
        })
    except Exception as e:
        os.remove(caminho)
        return jsonify({'erro': str(e)}), 500


@app.route('/download/<session_id>/<nome_arquivo>')
def download(session_id, nome_arquivo):
    caminho = os.path.join(app.config['OUTPUT_FOLDER'], session_id, nome_arquivo)
    if not os.path.exists(caminho):
        return jsonify({'erro': 'Arquivo não encontrado'}), 404
    return send_file(caminho, as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True, port=5000, threaded=True)
```

**Step 2: Testar manualmente**

```bash
python app.py
```

Em outro terminal:
```bash
curl -X POST http://localhost:5000/upload -F "arquivo=@caminho/para/teste.pdf"
```

Esperado: JSON com `session_id`, `paginas`, `total_lotes`.

**Step 3: Commit**

```bash
git add app.py
git commit -m "feat: rotas Flask para upload e informações do PDF"
```

---

## Task 9: Processamento em background + SSE

**Files:**
- Modify: `C:\Users\Henrique\ocr-pdf\app.py`

**Step 1: Adicionar estado global de sessões e rota /process**

```python
# Adicionar em app.py (após os imports existentes)
import threading
import json
import time
from flask import Response, stream_with_context
from ocr_engine import processar_lote, calcular_lotes, obter_info_pdf

# Estado das sessões em memória
sessoes = {}  # session_id -> dict com progresso e arquivos

def processar_em_background(session_id, caminho_pdf, lotes, formatos, pasta_saida):
    sessao = sessoes[session_id]
    os.makedirs(pasta_saida, exist_ok=True)

    for i, (inicio, fim) in enumerate(lotes):
        numero_lote = i + 1
        sessao['lote_atual'] = numero_lote
        sessao['pagina_atual'] = 0
        sessao['total_paginas_lote'] = fim - inicio + 1

        def progresso(pag_atual, total):
            sessao['pagina_atual'] = pag_atual

        try:
            arquivos = processar_lote(
                caminho_pdf, numero_lote, inicio, fim,
                pasta_saida, formatos, progresso
            )
            sessao['lotes_concluidos'].append({
                'numero': numero_lote,
                'arquivos': {k: os.path.basename(v) for k, v in arquivos.items()}
            })
        except Exception as e:
            sessao['erro'] = str(e)
            sessao['status'] = 'erro'
            return

        if sessao.get('cancelar'):
            sessao['status'] = 'cancelado'
            return

    sessao['status'] = 'concluido'
```

```python
# Adicionar rota /process em app.py
@app.route('/process', methods=['POST'])
def process():
    dados = request.get_json()
    session_id = dados.get('session_id')
    formatos = dados.get('formatos', {'pesquisavel': True, 'limpo': True, 'txt': True})
    tamanho_lote = int(dados.get('tamanho_lote', 500))

    caminho_pdf = os.path.join(app.config['UPLOAD_FOLDER'], f'{session_id}.pdf')
    if not os.path.exists(caminho_pdf):
        return jsonify({'erro': 'Sessão não encontrada'}), 404

    info = obter_info_pdf(caminho_pdf)
    lotes = calcular_lotes(info['paginas'], tamanho_lote)
    pasta_saida = os.path.join(app.config['OUTPUT_FOLDER'], session_id)

    sessoes[session_id] = {
        'status': 'processando',
        'total_lotes': len(lotes),
        'lote_atual': 0,
        'pagina_atual': 0,
        'total_paginas_lote': 0,
        'lotes_concluidos': [],
        'cancelar': False
    }

    thread = threading.Thread(
        target=processar_em_background,
        args=(session_id, caminho_pdf, lotes, formatos, pasta_saida)
    )
    thread.daemon = True
    thread.start()

    return jsonify({'ok': True})


@app.route('/progress/<session_id>')
def progress(session_id):
    def gerar_eventos():
        while True:
            if session_id not in sessoes:
                yield f"data: {json.dumps({'erro': 'sessão não encontrada'})}\n\n"
                break

            sessao = sessoes[session_id]
            yield f"data: {json.dumps(sessao)}\n\n"

            if sessao['status'] in ('concluido', 'erro', 'cancelado'):
                break

            time.sleep(1)

    return Response(
        stream_with_context(gerar_eventos()),
        mimetype='text/event-stream',
        headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'}
    )


@app.route('/cancel/<session_id>', methods=['POST'])
def cancel(session_id):
    if session_id in sessoes:
        sessoes[session_id]['cancelar'] = True
    return jsonify({'ok': True})
```

**Step 2: Commit**

```bash
git add app.py
git commit -m "feat: processamento em background e streaming de progresso via SSE"
```

---

## Task 10: Frontend HTML

**Files:**
- Modify: `C:\Users\Henrique\ocr-pdf\templates\index.html`

**Step 1: Escrever HTML completo**

```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OCR — Conversor de PDF</title>
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>OCR — Conversor de PDF Digitalizado</h1>
            {% if not config.tesseract_ok or not config.poppler_ok %}
            <div class="alerta-erro">
                {% if not config.tesseract_ok %}
                <p>⚠️ Tesseract não encontrado. Instale o Tesseract OCR.</p>
                {% endif %}
                {% if not config.poppler_ok %}
                <p>⚠️ Poppler não encontrado no caminho configurado.</p>
                {% endif %}
            </div>
            {% endif %}
        </header>

        <!-- Seção 1: Upload -->
        <section id="secao-upload">
            <div id="area-drop" class="area-drop">
                <p>Arraste um PDF aqui ou</p>
                <label for="input-arquivo" class="btn-secundario">Selecionar arquivo</label>
                <input type="file" id="input-arquivo" accept=".pdf" hidden>
                <p id="nome-arquivo" class="nome-arquivo"></p>
            </div>

            <div class="opcoes">
                <fieldset>
                    <legend>Formatos de saída</legend>
                    <label><input type="checkbox" id="opt-pesquisavel" checked> PDF pesquisável</label>
                    <label><input type="checkbox" id="opt-limpo" checked> PDF limpo (só texto)</label>
                    <label><input type="checkbox" id="opt-txt" checked> Arquivo .txt</label>
                </fieldset>

                <fieldset>
                    <legend>Tamanho do lote</legend>
                    <label>Páginas por lote:
                        <input type="number" id="tamanho-lote" value="500" min="10" max="2000">
                    </label>
                </fieldset>
            </div>

            <div id="info-pdf" class="info-pdf hidden"></div>

            <button id="btn-iniciar" class="btn-primario" disabled>Iniciar OCR</button>
        </section>

        <!-- Seção 2: Progresso -->
        <section id="secao-progresso" class="hidden">
            <h2>Progresso</h2>
            <p id="texto-progresso">Iniciando...</p>
            <div class="barra-progresso">
                <div id="barra-fill" class="barra-fill" style="width:0%"></div>
            </div>
            <p id="texto-percentual">0%</p>
            <button id="btn-cancelar" class="btn-perigo">Cancelar</button>
        </section>

        <!-- Seção 3: Downloads -->
        <section id="secao-downloads" class="hidden">
            <h2>Arquivos Gerados</h2>
            <div id="lista-downloads"></div>
        </section>
    </div>

    <script src="/static/app.js"></script>
</body>
</html>
```

**Step 2: Verificar que a página renderiza**

```bash
python app.py
```

Abrir `http://localhost:5000`. Esperado: interface visível sem erros no console.

**Step 3: Commit**

```bash
git add templates/index.html
git commit -m "feat: interface HTML do conversor OCR"
```

---

## Task 11: JavaScript do frontend

**Files:**
- Modify: `C:\Users\Henrique\ocr-pdf\static\app.js`

**Step 1: Escrever app.js**

```javascript
let sessionId = null;
let eventoSource = null;

const areaDrop = document.getElementById('area-drop');
const inputArquivo = document.getElementById('input-arquivo');
const nomeArquivo = document.getElementById('nome-arquivo');
const infoPdf = document.getElementById('info-pdf');
const btnIniciar = document.getElementById('btn-iniciar');
const btnCancelar = document.getElementById('btn-cancelar');
const secaoProgresso = document.getElementById('secao-progresso');
const secaoDownloads = document.getElementById('secao-downloads');
const textoProgresso = document.getElementById('texto-progresso');
const barraFill = document.getElementById('barra-fill');
const textoPercentual = document.getElementById('texto-percentual');
const listaDownloads = document.getElementById('lista-downloads');

// Drag & drop
areaDrop.addEventListener('dragover', e => { e.preventDefault(); areaDrop.classList.add('drag-over'); });
areaDrop.addEventListener('dragleave', () => areaDrop.classList.remove('drag-over'));
areaDrop.addEventListener('drop', e => {
    e.preventDefault();
    areaDrop.classList.remove('drag-over');
    const arquivo = e.dataTransfer.files[0];
    if (arquivo) processarArquivoSelecionado(arquivo);
});
inputArquivo.addEventListener('change', e => {
    if (e.target.files[0]) processarArquivoSelecionado(e.target.files[0]);
});

async function processarArquivoSelecionado(arquivo) {
    if (!arquivo.name.toLowerCase().endsWith('.pdf')) {
        alert('Por favor, selecione um arquivo PDF.');
        return;
    }

    nomeArquivo.textContent = `📄 ${arquivo.name}`;
    btnIniciar.disabled = true;
    infoPdf.textContent = 'Carregando informações do PDF...';
    infoPdf.classList.remove('hidden');

    const formData = new FormData();
    formData.append('arquivo', arquivo);
    formData.append('tamanho_lote', document.getElementById('tamanho-lote').value);

    try {
        const resp = await fetch('/upload', { method: 'POST', body: formData });
        const dados = await resp.json();

        if (dados.erro) { infoPdf.textContent = `Erro: ${dados.erro}`; return; }

        sessionId = dados.session_id;
        infoPdf.innerHTML = `
            <strong>${dados.paginas.toLocaleString('pt-BR')} páginas</strong> detectadas.
            Serão processados <strong>${dados.total_lotes} lote(s)</strong>
            de até ${document.getElementById('tamanho-lote').value} páginas cada.
        `;
        btnIniciar.disabled = false;
    } catch (e) {
        infoPdf.textContent = `Erro de comunicação: ${e.message}`;
    }
}

btnIniciar.addEventListener('click', async () => {
    if (!sessionId) return;

    const formatos = {
        pesquisavel: document.getElementById('opt-pesquisavel').checked,
        limpo: document.getElementById('opt-limpo').checked,
        txt: document.getElementById('opt-txt').checked
    };

    if (!formatos.pesquisavel && !formatos.limpo && !formatos.txt) {
        alert('Selecione pelo menos um formato de saída.');
        return;
    }

    document.getElementById('secao-upload').classList.add('hidden');
    secaoProgresso.classList.remove('hidden');
    secaoDownloads.classList.remove('hidden');

    await fetch('/process', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            session_id: sessionId,
            formatos,
            tamanho_lote: parseInt(document.getElementById('tamanho-lote').value)
        })
    });

    iniciarSSE();
});

function iniciarSSE() {
    eventoSource = new EventSource(`/progress/${sessionId}`);
    eventoSource.onmessage = e => {
        const dados = JSON.parse(e.data);
        atualizarProgresso(dados);

        if (['concluido', 'erro', 'cancelado'].includes(dados.status)) {
            eventoSource.close();
        }
    };
}

function atualizarProgresso(dados) {
    const totalLotes = dados.total_lotes || 1;
    const loteAtual = dados.lote_atual || 0;
    const pagAtual = dados.pagina_atual || 0;
    const totalPagLote = dados.total_paginas_lote || 1;

    const progGlobal = ((loteAtual - 1 + pagAtual / totalPagLote) / totalLotes) * 100;
    const pct = Math.min(Math.round(progGlobal), 100);

    barraFill.style.width = `${pct}%`;
    textoPercentual.textContent = `${pct}%`;

    if (dados.status === 'processando') {
        textoProgresso.textContent = `Lote ${loteAtual} de ${totalLotes} — Página ${pagAtual}/${totalPagLote}`;
    } else if (dados.status === 'concluido') {
        textoProgresso.textContent = '✅ Processamento concluído!';
        barraFill.style.width = '100%';
        textoPercentual.textContent = '100%';
        btnCancelar.disabled = true;
    } else if (dados.status === 'erro') {
        textoProgresso.textContent = `❌ Erro: ${dados.erro}`;
    } else if (dados.status === 'cancelado') {
        textoProgresso.textContent = '⚠️ Processamento cancelado.';
    }

    // Atualizar lista de downloads
    listaDownloads.innerHTML = '';
    for (const lote of (dados.lotes_concluidos || [])) {
        const div = document.createElement('div');
        div.className = 'lote-concluido';
        div.innerHTML = `<strong>Lote ${lote.numero}</strong>`;
        for (const [tipo, nome] of Object.entries(lote.arquivos)) {
            const label = { pesquisavel: 'PDF Pesquisável', limpo: 'PDF Limpo', txt: 'TXT' }[tipo] || tipo;
            div.innerHTML += ` <a href="/download/${sessionId}/${nome}" class="btn-download" download>${label}</a>`;
        }
        listaDownloads.appendChild(div);
    }
}

btnCancelar.addEventListener('click', async () => {
    if (!sessionId) return;
    await fetch(`/cancel/${sessionId}`, { method: 'POST' });
    btnCancelar.disabled = true;
});
```

**Step 2: Commit**

```bash
git add static/app.js
git commit -m "feat: JavaScript do frontend com upload, SSE e downloads"
```

---

## Task 12: CSS da interface

**Files:**
- Modify: `C:\Users\Henrique\ocr-pdf\static\style.css`

**Step 1: Escrever style.css**

```css
:root {
    --cor-primaria: #2563eb;
    --cor-perigo: #dc2626;
    --cor-sucesso: #16a34a;
    --cor-fundo: #f1f5f9;
    --cor-cartao: #ffffff;
    --cor-borda: #e2e8f0;
    --raio: 8px;
}

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
    font-family: 'Segoe UI', system-ui, sans-serif;
    background: var(--cor-fundo);
    color: #1e293b;
    padding: 2rem;
}

.container {
    max-width: 760px;
    margin: 0 auto;
}

header h1 {
    font-size: 1.5rem;
    margin-bottom: 1.5rem;
    color: #0f172a;
}

section {
    background: var(--cor-cartao);
    border: 1px solid var(--cor-borda);
    border-radius: var(--raio);
    padding: 1.5rem;
    margin-bottom: 1.5rem;
}

.hidden { display: none !important; }

/* Upload */
.area-drop {
    border: 2px dashed var(--cor-borda);
    border-radius: var(--raio);
    padding: 2.5rem;
    text-align: center;
    cursor: pointer;
    transition: border-color 0.2s, background 0.2s;
}
.area-drop.drag-over {
    border-color: var(--cor-primaria);
    background: #eff6ff;
}
.area-drop p { color: #64748b; margin-bottom: 0.75rem; }
.nome-arquivo { font-weight: 600; color: #0f172a; margin-top: 0.5rem; }

.opcoes {
    display: flex;
    gap: 1.5rem;
    margin: 1.25rem 0;
    flex-wrap: wrap;
}

fieldset {
    border: 1px solid var(--cor-borda);
    border-radius: var(--raio);
    padding: 0.75rem 1rem;
    flex: 1;
    min-width: 200px;
}
legend { font-weight: 600; padding: 0 0.4rem; font-size: 0.875rem; color: #475569; }
label { display: block; margin-top: 0.4rem; font-size: 0.9rem; cursor: pointer; }
label input[type="checkbox"] { margin-right: 0.4rem; }
input[type="number"] {
    width: 80px;
    padding: 0.25rem 0.5rem;
    border: 1px solid var(--cor-borda);
    border-radius: 4px;
    margin-left: 0.4rem;
}

.info-pdf {
    background: #f0f9ff;
    border: 1px solid #bae6fd;
    border-radius: var(--raio);
    padding: 0.75rem 1rem;
    margin: 0.75rem 0;
    font-size: 0.9rem;
}

/* Botões */
.btn-primario, .btn-secundario, .btn-perigo, .btn-download {
    display: inline-block;
    padding: 0.55rem 1.25rem;
    border-radius: var(--raio);
    border: none;
    font-size: 0.9rem;
    font-weight: 500;
    cursor: pointer;
    text-decoration: none;
    transition: opacity 0.15s;
}
.btn-primario { background: var(--cor-primaria); color: white; }
.btn-secundario { background: #e2e8f0; color: #1e293b; }
.btn-perigo { background: var(--cor-perigo); color: white; }
.btn-download { background: var(--cor-sucesso); color: white; font-size: 0.8rem; padding: 0.3rem 0.7rem; margin-left: 0.5rem; }
button:disabled { opacity: 0.4; cursor: not-allowed; }

/* Progresso */
.barra-progresso {
    background: var(--cor-borda);
    border-radius: 999px;
    height: 12px;
    margin: 0.75rem 0 0.25rem;
    overflow: hidden;
}
.barra-fill {
    height: 100%;
    background: var(--cor-primaria);
    border-radius: 999px;
    transition: width 0.5s ease;
}
#texto-progresso { font-size: 0.9rem; color: #475569; margin-bottom: 0.5rem; }
#texto-percentual { font-weight: 700; font-size: 1.1rem; color: var(--cor-primaria); }

/* Downloads */
.lote-concluido {
    padding: 0.6rem 0;
    border-bottom: 1px solid var(--cor-borda);
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 0.25rem;
}
.lote-concluido:last-child { border-bottom: none; }

.alerta-erro {
    background: #fef2f2;
    border: 1px solid #fecaca;
    border-radius: var(--raio);
    padding: 0.75rem 1rem;
    margin-bottom: 1rem;
    font-size: 0.9rem;
    color: #991b1b;
}
```

**Step 2: Commit**

```bash
git add static/style.css
git commit -m "feat: CSS da interface OCR"
```

---

## Task 13: start.bat e teste de integração final

**Files:**
- Create: `C:\Users\Henrique\ocr-pdf\start.bat`

**Step 1: Criar start.bat**

```bat
@echo off
title OCR - Conversor de PDF
cd /d C:\Users\Henrique\ocr-pdf
call venv\Scripts\activate
echo.
echo ============================================
echo  OCR - Conversor de PDF Digitalizado
echo  Acesse: http://localhost:5000
echo  Pressione Ctrl+C para parar o servidor
echo ============================================
echo.
python app.py
pause
```

**Step 2: Teste de integração completo**

1. Dar duplo clique em `start.bat`
2. Abrir `http://localhost:5000` no navegador
3. Verificar que a interface carrega sem alertas de erro
4. Selecionar um PDF pequeno (10-20 páginas)
5. Confirmar que o número de páginas e lotes aparece corretamente
6. Iniciar o OCR com todos os formatos marcados
7. Verificar que a barra de progresso avança
8. Verificar que os arquivos aparecem para download ao final
9. Baixar cada arquivo e verificar que estão corretos

**Step 3: Commit final**

```bash
git add start.bat
git commit -m "feat: start.bat e configuração final do projeto OCR"
```

---

## Resumo de Instalações Necessárias

| Software | Link / Comando | Observação |
|---|---|---|
| Tesseract OCR | https://github.com/UB-Mannheim/tesseract/wiki | Marcar "Portuguese" na instalação |
| Python 3.x | https://www.python.org | Marcar "Add to PATH" |
| Dependências pip | `pip install flask pytesseract Pillow pdf2image pypdf fpdf2` | Após ativar venv |
| Poppler | Já instalado | `C:\Users\Henrique\poppler\poppler-24.08.0\` |
