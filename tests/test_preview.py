"""Testes do preview (Fase 5)."""
import os
import shutil

import pytest

import preview


def test_soffice_detectado():
    assert preview.soffice() in (shutil.which("soffice"), shutil.which("libreoffice"))


def test_para_pdf_sem_soffice(monkeypatch, tmp_path):
    monkeypatch.setattr(preview.shutil, "which", lambda nome: None)
    arquivo = tmp_path / "doc.odt"
    arquivo.write_bytes(b"x")
    with pytest.raises(RuntimeError, match="LibreOffice"):
        preview.para_pdf(str(arquivo))


def test_para_pdf_arquivo_inexistente(monkeypatch, tmp_path):
    monkeypatch.setattr(preview.shutil, "which", lambda nome: "/usr/bin/soffice")
    with pytest.raises(FileNotFoundError):
        preview.para_pdf(str(tmp_path / "nao_existe.odt"))


def _criar_docx(caminho, texto="AutoDoc preview"):
    from docx import Document

    documento = Document()
    documento.add_paragraph(texto)
    documento.save(caminho)


@pytest.mark.skipif(not preview.soffice(), reason="LibreOffice não instalado")
def test_renderizar_documento_real(tmp_path):
    docx = tmp_path / "teste.docx"
    _criar_docx(str(docx))
    paginas = preview.renderizar(str(docx), max_paginas=1)
    assert len(paginas) == 1
    assert os.path.isfile(paginas[0])
    assert os.path.getsize(paginas[0]) > 1000


@pytest.mark.skipif(not preview.soffice(), reason="LibreOffice não instalado")
def test_para_pdf_gera_pdf(tmp_path):
    docx = tmp_path / "teste.docx"
    _criar_docx(str(docx))
    pdf = preview.para_pdf(str(docx), str(tmp_path))
    assert pdf.endswith(".pdf")
    assert os.path.getsize(pdf) > 500
