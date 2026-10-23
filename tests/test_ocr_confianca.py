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


def test_extrair_texto_com_confianca_preserva_texto_curto(monkeypatch, _sem_preprocesso):
    """Valores curtos (UF, SIM, número) são dados válidos, não ruído."""
    monkeypatch.setattr(
        pytesseract, 'image_to_data',
        lambda img, lang=None, config=None, output_type=None: {
            'text': ['MG'],
            'conf': [99],
        },
    )
    texto, conf = extrair_texto_com_confianca(object())
    assert texto == 'MG'
    assert conf == 99.0


def test_extrair_texto_com_confianca_tenta_cinza_quando_vazio(monkeypatch, _sem_preprocesso):
    """Se a binarização não ler nada, tenta a mesma região em escala de cinza."""
    monkeypatch.setattr('ocr._para_cinza', lambda img: img)
    chamadas = []

    def fake(img, lang=None, config=None, output_type=None):
        chamadas.append((img, config))
        if len(chamadas) == 1:
            return {'text': [], 'conf': []}
        return {'text': ['JOAO'], 'conf': [80]}

    monkeypatch.setattr(pytesseract, 'image_to_data', fake)
    texto, _conf = extrair_texto_com_confianca(object())
    assert texto == 'JOAO'
    assert len(chamadas) == 2


def test_extrair_texto_com_confianca_usa_psm7_na_ultima_tentativa(monkeypatch, _sem_preprocesso):
    """Sem leitura em bloco, tenta segmentação de linha única."""
    monkeypatch.setattr('ocr._para_cinza', lambda img: img)
    chamadas = []

    def fake(img, lang=None, config=None, output_type=None):
        chamadas.append(config)
        if len(chamadas) < 3:
            return {'text': [], 'conf': []}
        return {'text': ['LINHA'], 'conf': [70]}

    monkeypatch.setattr(pytesseract, 'image_to_data', fake)
    texto, _ = extrair_texto_com_confianca(object())
    assert texto == 'LINHA'
    assert 'psm 7' in chamadas[-1]


def test_extrair_texto_com_confianca_propaga_erro(monkeypatch, _sem_preprocesso):
    """Erro do Tesseract deve subir para a UI mostrar o motivo real."""
    def fake(img, lang=None, config=None, output_type=None):
        raise RuntimeError('tesseract não encontrado')

    monkeypatch.setattr(pytesseract, 'image_to_data', fake)
    with pytest.raises(RuntimeError, match='tesseract'):
        extrair_texto_com_confianca(object())


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
