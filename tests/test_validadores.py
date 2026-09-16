"""Tests for validadores module"""
import os
import tempfile
from validadores import validar_extensao, obter_filetypes_modelo, obter_filetypes_anexo


class TestValidarExtensao:
    def test_docx_valido(self):
        ok, ext, msg = validar_extensao("doc.docx", "modelo")
        assert ok is True
        assert ext == ".docx"

    def test_odt_valido(self):
        ok, ext, msg = validar_extensao("doc.odt", "modelo")
        assert ok is True
        assert ext == ".odt"

    def test_invalido_modelo(self):
        ok, ext, msg = validar_extensao("doc.pdf", "modelo")
        assert ok is False
        assert ext == ".pdf"

    def test_pdf_valido_anexo(self):
        ok, ext, msg = validar_extensao("scan.pdf", "anexo")
        assert ok is True
        assert ext == ".pdf"

    def test_jpg_valido_anexo(self):
        ok, ext, msg = validar_extensao("foto.jpg", "anexo")
        assert ok is True

    def test_heic_valido_anexo(self):
        ok, ext, msg = validar_extensao("foto.heic", "anexo")
        assert ok is True

    def test_invalido_anexo(self):
        ok, ext, msg = validar_extensao("doc.xlsx", "anexo")
        assert ok is False

    def test_tipo_invalido(self):
        ok, ext, msg = validar_extensao("doc.docx", "outro")
        assert ok is False
        assert ext is None


class TestFiletypes:
    def test_filetypes_modelo_returns_list(self):
        ft = obter_filetypes_modelo()
        assert isinstance(ft, list)
        assert len(ft) >= 2

    def test_filetypes_anexo_returns_list(self):
        ft = obter_filetypes_anexo()
        assert isinstance(ft, list)
        assert len(ft) >= 2
