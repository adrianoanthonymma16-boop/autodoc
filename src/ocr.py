"""
Módulo de OCR (Optical Character Recognition)
Responsável por pré-processar imagens e extrair texto usando Tesseract
"""

import sys

import cv2
import numpy as np
import pytesseract
from PIL import Image

from config import OCR_CLIPLIMIT, OCR_RESIZE_FATOR, OCR_TILE_GRID, TESSERACT_CONFIG, TESSERACT_LANG
from resources import resource_path


def _configurar_tesseract():
    """Usa o Tesseract embutido no instalador Windows, quando existir."""
    if sys.platform != "win32":
        return
    bundled = resource_path("tesseract", "tesseract.exe")
    if bundled.is_file():
        pytesseract.pytesseract.tesseract_cmd = str(bundled)


_configurar_tesseract()


def _para_cinza(imagem_pil):
    """Normaliza a imagem e devolve o recorte em escala de cinza ampliado.

    A binarização OTSU ajuda em digitalizações, mas apaga texto claro sobre
    fundo escuro, carimbos e fotos com sombra. Por isso o OCR tenta também
    esta versão sem limiar quando a primeira leitura não devolve nada.
    """
    # Normaliza modo PIL para RGB
    if imagem_pil.mode == "RGBA":
        bg = Image.new("RGB", imagem_pil.size, (255, 255, 255))
        bg.paste(imagem_pil, mask=imagem_pil.split()[3])
        imagem_pil = bg
    elif imagem_pil.mode == "LA" or imagem_pil.mode == "P" or imagem_pil.mode == "L" or imagem_pil.mode != "RGB":
        imagem_pil = imagem_pil.convert("RGB")

    # Converte PIL para OpenCV (RGB para BGR)
    img = cv2.cvtColor(np.array(imagem_pil), cv2.COLOR_RGB2BGR)

    # Aumenta resolução
    h, w = img.shape[:2]
    img = cv2.resize(img, (w * OCR_RESIZE_FATOR, h * OCR_RESIZE_FATOR),
                      interpolation=cv2.INTER_CUBIC)

    # Escala de cinza
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # CLAHE (Contraste Local Adaptativo)
    clahe = cv2.createCLAHE(clipLimit=OCR_CLIPLIMIT, tileGridSize=OCR_TILE_GRID)
    return clahe.apply(gray)


def preprocessar_imagem(imagem_pil):
    """
    Pré-processa a imagem para melhorar a leitura do OCR

    Etapas:
    1. Converte PIL para OpenCV
    2. Aumenta resolução (resize)
    3. Converte para escala de cinza
    4. Aplica CLAHE para contraste local
    5. Binarização OTSU (preto e branco)

    Args:
        imagem_pil (PIL.Image): Imagem original

    Returns:
        numpy.ndarray: Imagem processada em preto e branco
    """
    gray = _para_cinza(imagem_pil)
    # Binarização OTSU (preto e branco)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return binary


def calcular_confianca(data):
    """
    Calcula confiança média ponderada (por nº de caracteres) de um resultado
    de pytesseract.image_to_data.

    Args:
        data (dict): {'conf': [...], 'text': [...]}

    Returns:
        float: confiança média 0..100 (0.0 quando não há palavras válidas)
    """
    textos = data.get('text', [])
    confs = data.get('conf', [])
    peso_total = 0.0
    soma = 0.0
    for texto, conf in zip(textos, confs, strict=False):
        try:
            conf_num = float(conf)
        except (TypeError, ValueError):
            continue
        if conf_num < 0:
            continue
        peso = len(texto.strip())
        if peso == 0:
            continue
        peso_total += peso
        soma += conf_num * peso
    if peso_total == 0:
        return 0.0
    return round(soma / peso_total, 1)


_LANGS = None


def _langs_disponiveis():
    """Lista os idiomas do Tesseract, tolerando ambientes sem o binário."""
    global _LANGS
    if _LANGS is None:
        try:
            _LANGS = set(pytesseract.get_languages(config=''))
        except Exception:
            _LANGS = set()
    return _LANGS


def _lang_efetiva():
    """Usa o idioma do projeto; cai para inglês se ele não estiver instalado."""
    langs = _langs_disponiveis()
    if not langs or TESSERACT_LANG in langs:
        return TESSERACT_LANG
    return 'eng' if 'eng' in langs else sorted(langs)[0]


def _ocr_data(imagem, config):
    data = pytesseract.image_to_data(
        imagem,
        lang=_lang_efetiva(),
        config=config,
        output_type=pytesseract.Output.DICT,
    )
    texto = ' '.join(
        t for t in data.get('text', []) if t and t.strip()
    )
    texto = ' '.join(texto.split())
    return texto, calcular_confianca(data)


def extrair_texto_com_confianca(imagem_pil):
    """
    OCR com confiança por região usando image_to_data.

    Tenta a binarização OTSU (melhor para digitalização) e, se nada vier,
    repete em escala de cinza e com segmentação de linha única. Valores
    curtos (ex.: "MG", "SIM", "1") são válidos e não podem ser descartados.

    Returns:
        tuple[str, float]: (texto limpo, confiança 0..100).
    """
    texto, conf = _ocr_data(preprocessar_imagem(imagem_pil), TESSERACT_CONFIG)
    if texto:
        return texto, conf
    cinza = _para_cinza(imagem_pil)
    for config in (TESSERACT_CONFIG, '--psm 7'):
        texto, conf = _ocr_data(cinza, config)
        if texto:
            return texto, conf
    return "", 0.0


def extrair_texto_da_regiao(imagem_pil):
    """
    Extrai texto de uma região da imagem usando Tesseract

    Args:
        imagem_pil (PIL.Image): Imagem da região a ser processada

    Returns:
        str: Texto extraído (limpo)
    """
    # Pré-processa
    imagem_processada = preprocessar_imagem(imagem_pil)

    # Aplica OCR
    texto = pytesseract.image_to_string(
        imagem_processada,
        lang=TESSERACT_LANG,
        config=TESSERACT_CONFIG
    )

    # Limpa o texto
    texto = texto.strip()
    texto = texto.replace('\n', ' ')
    texto = ' '.join(texto.split())

    return texto


def extrair_recorte_com_confianca(imagem_original, coordenadas):
    """
    OCR com confiança de um recorte da imagem.

    Args:
        imagem_original (PIL.Image): Imagem completa
        coordenadas (dict): {'x1':, 'y1':, 'x2':, 'y2'}

    Returns:
        tuple[str, float]: (texto, confiança 0..100)
    """
    regiao = imagem_original.crop((
        coordenadas['x1'],
        coordenadas['y1'],
        coordenadas['x2'],
        coordenadas['y2']
    ))
    return extrair_texto_com_confianca(regiao)


def extrair_texto_do_recorte(imagem_original, coordenadas):
    """
    Extrai texto de um recorte específico da imagem

    Args:
        imagem_original (PIL.Image): Imagem completa
        coordenadas (dict): {'x1':, 'y1':, 'x2':, 'y2':}

    Returns:
        str: Texto extraído
    """
    # Recorta a região
    regiao = imagem_original.crop((
        coordenadas['x1'],
        coordenadas['y1'],
        coordenadas['x2'],
        coordenadas['y2']
    ))

    # Extrai texto
    return extrair_texto_da_regiao(regiao)
