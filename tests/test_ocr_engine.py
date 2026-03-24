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
