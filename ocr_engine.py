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
