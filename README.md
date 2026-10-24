# OCR — Conversor de PDF Digitalizado

Aplicação web local para converter PDFs digitalizados (imagens) em PDFs pesquisáveis, PDFs com texto limpo e arquivos TXT, usando OCR via Tesseract.

## Funcionalidades

- Upload de PDFs de qualquer tamanho (até 2 GB)
- Processamento por lotes (padrão: 500 páginas por lote) para controle de RAM
- Três formatos de saída por lote:
  - **PDF pesquisável** — imagem original com texto invisível sobreposto
  - **PDF limpo** — somente o texto extraído, sem imagens
  - **TXT** — texto puro com marcadores de página
- Progresso em tempo real via Server-Sent Events (SSE)
- Cancelamento durante o processamento
- Download individual de cada arquivo gerado

## Requisitos

- Python 3.10+
- [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) instalado em `C:\Program Files\Tesseract-OCR\`
- [Poppler for Windows](https://github.com/oschwartz10612/poppler-windows/releases/) descompactado (caminho configurado em `ocr_engine.py`)

## Instalação

```bash
# Clone o repositório
git clone https://github.com/winklan/ocr-pdf.git
cd ocr-pdf

# Crie e ative o ambiente virtual
python -m venv venv
venv\Scripts\activate

# Instale as dependências
pip install -r requirements.txt
```

Antes de rodar, ajuste os caminhos em `ocr_engine.py` conforme sua instalação:

```python
TESSERACT_PATH = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
POPPLER_PATH   = r'C:\Users\<seu-usuario>\poppler-26.09.0\Library\bin'
```

## Uso

### Opção 1 — Duplo clique

Execute `start.bat` para iniciar o servidor automaticamente.

### Opção 2 — Terminal

```bash
venv\Scripts\activate
python app.py
```

Acesse **http://localhost:5000** no navegador.

## Estrutura do projeto

```
ocr-pdf/
├── app.py              # Servidor Flask (rotas e gerenciamento de sessões)
├── ocr_engine.py       # Motor OCR (Tesseract + Poppler)
├── requirements.txt    # Dependências Python
├── start.bat           # Atalho de inicialização para Windows
├── templates/
│   └── index.html      # Interface web
├── static/
│   ├── style.css       # Estilos
│   └── app.js          # JavaScript do frontend
└── tests/              # Testes automatizados (pytest)
```

## Dependências Python

| Pacote       | Uso                                      |
|--------------|------------------------------------------|
| Flask        | Servidor web                             |
| pytesseract  | Interface Python para o Tesseract OCR    |
| Pillow       | Manipulação de imagens                   |
| pdf2image    | Conversão de páginas PDF em imagens      |
| pypdf        | Mesclagem de PDFs pesquisáveis           |
| fpdf2        | Geração de PDF limpo a partir de texto   |
| pytest       | Testes automatizados                     |

## Testes

```bash
pytest tests/
```

## Licença

Uso pessoal / interno.
