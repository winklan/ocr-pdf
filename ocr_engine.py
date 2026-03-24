import os
import io
import pytesseract
from pdf2image import pdfinfo_from_path, convert_from_path
from fpdf import FPDF
from pypdf import PdfWriter, PdfReader

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


def calcular_lotes(total_paginas, tamanho_lote=500):
    """Retorna lista de tuplas (pagina_inicio, pagina_fim)."""
    lotes = []
    inicio = 1
    while inicio <= total_paginas:
        fim = min(inicio + tamanho_lote - 1, total_paginas)
        lotes.append((inicio, fim))
        inicio = fim + 1
    return lotes


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
        reader = PdfReader(io.BytesIO(pdf_bytes))
        for page in reader.pages:
            writer.add_page(page)
    with open(caminho_saida, 'wb') as f:
        writer.write(f)
