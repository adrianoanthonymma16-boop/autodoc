"""Seletor de arquivos: filtragem, ordenação e ocultos (sem Tk)."""
import os
from dataclasses import FrozenInstanceError

import pytest

from ui.file_dialog import (
    Entrada,
    _sufixos_do_rotulo,
    formatar_data,
    formatar_tamanho,
    listar,
    locais_rapidos,
    sufixos_dos_filetypes,
)


def _criar(tmp_path, *nomes):
    for nome in nomes:
        caminho = tmp_path / nome
        if nome.endswith("/"):
            caminho.mkdir()
        else:
            caminho.write_text("x", encoding="utf-8")
    return tmp_path


def test_oculta_arquivos_e_pastas_com_ponto(tmp_path):
    _criar(tmp_path, ".env", ".config/", "modelo.docx")
    nomes = [e.nome for e in listar(tmp_path)]
    assert nomes == ["modelo.docx"]


def test_mostra_ocultos_quando_pedido(tmp_path):
    _criar(tmp_path, ".env", "modelo.docx")
    nomes = [e.nome for e in listar(tmp_path, incluir_ocultos=True)]
    assert nomes == [".env", "modelo.docx"]


def test_pastas_primeiro_e_ordem_alfabetica(tmp_path):
    _criar(tmp_path, "zebra.docx", "Alfa.docx", "pasta_b/", "pasta_a/")
    entradas = listar(tmp_path)
    assert [e.nome for e in entradas] == ["pasta_a", "pasta_b", "Alfa.docx", "zebra.docx"]
    assert all(e.eh_dir for e in entradas[:2])


def test_filtra_por_sufixo(tmp_path):
    _criar(tmp_path, "a.docx", "b.odt", "c.csv")
    nomes = [e.nome for e in listar(tmp_path, sufixos=(".odt", ".docx"))]
    assert nomes == ["a.docx", "b.odt"]


def test_filtro_ignora_maiusculas(tmp_path):
    _criar(tmp_path, "MODELO.DOCX")
    assert [e.nome for e in listar(tmp_path, sufixos=(".docx",))] == ["MODELO.DOCX"]


def test_somente_diretorios(tmp_path):
    _criar(tmp_path, "sub/", "arquivo.txt")
    entradas = listar(tmp_path, somente_diretorios=True)
    assert [e.nome for e in entradas] == ["sub"]


def test_sufixos_dos_filetypes():
    filetypes = [("Documentos", "*.odt *.docx"), ("CSV", "*.csv"), ("Todos", "*.*")]
    assert sufixos_dos_filetypes(filetypes[:2]) == (".odt", ".docx", ".csv")
    assert sufixos_dos_filetypes(filetypes) == ()


def test_sufixos_do_rotulo():
    filetypes = [("Planilhas", "*.xlsx *.xlsm"), ("CSV", "*.csv")]
    assert _sufixos_do_rotulo(filetypes, "CSV") == (".csv",)
    assert _sufixos_do_rotulo(filetypes, "Inexistente") == ()


def test_formatar_tamanho():
    assert formatar_tamanho(0) == "0 B"
    assert formatar_tamanho(512) == "512 B"
    assert formatar_tamanho(1024) == "1 KB"
    assert formatar_tamanho(1536) == "1.5 KB"
    assert formatar_tamanho(1024 * 1024) == "1 MB"


def test_formatar_data_vazia():
    assert formatar_data(0) == ""
    assert ":" in formatar_data(1_700_000_000)


def test_locais_rapidos_so_existentes():
    locais = locais_rapidos()
    assert locais
    for _rotulo, _icone, caminho in locais:
        assert os.path.isdir(caminho)


def test_entrada_eh_frozen():
    entrada = Entrada("a.txt", "/tmp/a.txt", False, 1, 2.0)
    with pytest.raises(FrozenInstanceError):
        entrada.nome = "b"
