"""Testes do histórico (Fase 3: dados usados ficam registrados)."""
import os

import historico


def _isolar(monkeypatch, tmp_path):
    monkeypatch.setattr(historico, "HISTORY_PATH", str(tmp_path / "historico.json"))


def test_historico_guarda_dados(monkeypatch, tmp_path):
    _isolar(monkeypatch, tmp_path)
    historico.adicionar_ao_historico("/tmp/mod.odt", "odt", "/tmp/out.odt", 2, dados={"nome": "Ana"})
    lista = historico.listar_historico()
    assert len(lista) == 1
    assert lista[0]["dados"] == {"nome": "Ana"}


def test_historico_sem_dados_usa_dict_vazio(monkeypatch, tmp_path):
    _isolar(monkeypatch, tmp_path)
    historico.adicionar_ao_historico("/tmp/mod.odt", "odt", "/tmp/out.odt", 0)
    assert historico.listar_historico()[0]["dados"] == {}


def test_historico_limita_entradas(monkeypatch, tmp_path):
    _isolar(monkeypatch, tmp_path)
    for i in range(historico.MAX_ENTRIES + 5):
        historico.adicionar_ao_historico("/tmp/mod.odt", "odt", f"/tmp/out{i}.odt", 1)
    assert len(historico.carregar_historico()) == historico.MAX_ENTRIES


def test_historico_arquivo_inexistente(monkeypatch, tmp_path):
    _isolar(monkeypatch, tmp_path)
    assert historico.listar_historico() == []
    assert not os.path.exists(str(tmp_path / "historico.json"))
