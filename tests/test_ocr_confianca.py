"""Testes da confiança de OCR (Fase 1)."""
import pytesseract
import pytest

from ocr import calcular_confianca, extrair_recorte_com_confianca, extrair_texto_com_confianca


class _FakeData:
    @staticmethod
    def dict_(words, confs):
        return {'text': words, 'conf': confs}


def test_calcular_confianca_ponderada():
    data = {
        'text': ['JOAO', 'DA', 'SILVA'],
        'conf': [90, -1, 70],  # -1 = palavra vazia, deve ser ignorada
    }
    # média ponderada por nº de caracteres:
    # (90*4 + 70*5) / (4+5) = 78.9
    assert calcular_confianca(data) == 78.9


def test_calcular_confianca_vazio(monkeypatch):
    data = {'text': [], 'conf': []}
    assert calcular_confianca(data) == 0.0


@pytest.fixture
def _sem_preprocesso(monkeypatch):
    """Evita cv2 nos testes: pré-processamento vira identidade."""
    monkeypatch.setattr('ocr.preprocessar_imagem', lambda img: img)


def test_extrair_texto_com_confianca_limpeza(monkeypatch, _sem_preprocesso):
    monkeypatch.setattr(
        pytesseract, 'image_to_data',
        lambda img, lang=None, config=None, output_type=None: {
            'text': ['  Maria ', 'de', 'Souza  '],
            'conf': [85, -1, 95],
        },
    )
    texto, conf = extrair_texto_com_confianca(object())
    assert texto == 'Maria de Souza'
    # (85*5 + 95*5) / 10 = 90.0
    assert conf == 90.0


def test_extrair_texto_com_confianca_texto_curto(monkeypatch, _sem_preprocesso):
    """Texto <= 2 chars retorna vazio, como extrair_texto_da_regiao."""
    monkeypatch.setattr(
        pytesseract, 'image_to_data',
        lambda img, lang=None, config=None, output_type=None: {
            'text': ['ab'],
            'conf': [99],
        },
    )
    texto, conf = extrair_texto_com_confianca(object())
    assert texto == ''
    assert conf == 0.0


def test_extrair_texto_com_confianca_respeita_config(monkeypatch, _sem_preprocesso):
    """Deve chamar image_to_data com a config do projeto (psm 6, lang por)."""
    chamadas = {}

    def fake(img, lang=None, config=None, output_type=None):
        chamadas['lang'] = lang
        chamadas['config'] = config
        return {'text': ['OKCAR'], 'conf': [80]}

    monkeypatch.setattr(pytesseract, 'image_to_data', fake)
    extrair_texto_com_confianca(object())
    assert chamadas['lang'] == 'por'
    assert 'psm 6' in chamadas['config']


def test_extrair_recorte_com_confianca(monkeypatch, _sem_preprocesso):
    """Recorta a imagem antes de rodar OCR."""
    dados_ocr = {'text': ['TEXTO'], 'conf': [88]}
    captura = {}

    def fake_data(img, lang=None, config=None, output_type=None):
        captura['img'] = img
        return dados_ocr

    monkeypatch.setattr(pytesseract, 'image_to_data', fake_data)
    texto, conf = extrair_recorte_com_confianca(_FakeImagem(), {'x1': 10, 'y1': 20, 'x2': 110, 'y2': 60})
    assert texto == 'TEXTO'
    assert conf == 88.0
    assert captura['img'].box == (10, 20, 110, 60)


class _FakeImagem:
    def crop(self, box):
        return _Recorte(box)


class _Recorte:
    def __init__(self, box):
        self.box = box
