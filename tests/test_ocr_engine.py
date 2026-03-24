# tests/test_ocr_engine.py
import pytest
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ocr_engine import validar_configuracao, obter_info_pdf, calcular_lotes

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


def test_converter_paginas_retorna_lista_de_imagens():
    from ocr_engine import converter_paginas_em_imagens
    FIXTURE_PDF = os.path.join(os.path.dirname(__file__), 'fixtures', 'teste.pdf')
    if not os.path.exists(FIXTURE_PDF):
        pytest.skip("PDF de teste não encontrado")
    imagens = converter_paginas_em_imagens(FIXTURE_PDF, pagina_inicio=1, pagina_fim=1)
    assert len(imagens) == 1
    assert hasattr(imagens[0], 'size')  # é objeto PIL.Image
