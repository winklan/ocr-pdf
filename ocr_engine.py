import os
import io
import pytesseract
from pdf2image import pdfinfo_from_path, convert_from_path
from fpdf import FPDF
from pypdf import PdfWriter, PdfReader

# Caminhos das ferramentas
TESSERACT_PATH = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
POPPLER_PATH = r'C:\Users\Henrique\poppler-26.09.0\Library\bin'

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
        # Preservar caracteres Latin-1 (inclui ç, ã, á etc do português)
        # Caracteres fora do Latin-1 (ex: aspas tipográficas, travessão) são removidos
        texto_limpo = texto.encode('latin-1', errors='ignore').decode('latin-1')
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


def processar_lote(caminho_pdf, numero_lote, pagina_inicio, pagina_fim,
                   pasta_saida, formatos, callback_progresso=None, cancelar_fn=None):
    """
    Processa um lote de páginas e gera os arquivos de saída.

    formatos: dict com chaves 'pesquisavel', 'limpo', 'txt' (bool)
    callback_progresso: função(pagina_atual, total_paginas) chamada a cada página
    cancelar_fn: função() que retorna True se o processamento deve ser cancelado

    Retorna dict com caminhos dos arquivos gerados, ou None se cancelado.
    Processa uma página por vez para não esgotar a RAM.
    """
    total_paginas_lote = pagina_fim - pagina_inicio + 1
    textos = []
    pdfs_pesquisavel = []

    for i, pagina_abs in enumerate(range(pagina_inicio, pagina_fim + 1)):
        if cancelar_fn and cancelar_fn():
            return None

        # Converter apenas 1 página por vez — evita pico de RAM
        imagens = converter_paginas_em_imagens(caminho_pdf, pagina_abs, pagina_abs)
        imagem = imagens[0]

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
