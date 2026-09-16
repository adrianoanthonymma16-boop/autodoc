"""Tests for config module"""
import os
from config import (
    VERSAO, PASTA_APP, MODELO_EXTENSOES, ANEXO_EXTENSOES,
    TESSERACT_LANG, PASTA_MODELOS, REGISTRO_MODELOS,
    LIGHT_THEME, DARK_THEME,
)


def test_versao_is_string():
    assert isinstance(VERSAO, str)
    assert "." in VERSAO


def test_pasta_app_is_absolute():
    assert os.path.isabs(PASTA_APP)


def test_modelo_extensions_include_odt_docx():
    assert ".odt" in MODELO_EXTENSOES
    assert ".docx" in MODELO_EXTENSOES


def test_anexo_extensions_include_common():
    assert ".jpg" in ANEXO_EXTENSOES
    assert ".png" in ANEXO_EXTENSOES
    assert ".pdf" in ANEXO_EXTENSOES


def test_tesseract_lang_is_portuguese():
    assert TESSERACT_LANG == "por"


def test_modelos_dir_exists():
    assert os.path.isdir(PASTA_MODELOS)


def test_registro_modelos_path():
    assert REGISTRO_MODELOS.startswith(PASTA_MODELOS)
    assert REGISTRO_MODELOS.endswith("registros.json")


def test_themes_have_required_keys():
    required = {"canvas_bg", "listbox_bg", "listbox_fg", "text_bg", "text_fg", "select_bg", "select_fg"}
    assert required.issubset(set(LIGHT_THEME.keys()))
    assert required.issubset(set(DARK_THEME.keys()))


def test_themes_are_different():
    assert LIGHT_THEME["canvas_bg"] != DARK_THEME["canvas_bg"]
