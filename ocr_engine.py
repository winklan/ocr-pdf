import os
import pytesseract
from pdf2image import pdfinfo_from_path, convert_from_path

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
