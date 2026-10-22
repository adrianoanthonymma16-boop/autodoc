"""Testes das fichas reaproveitáveis (Fase 3)."""
import json

import fichas


def _isolar(monkeypatch, tmp_path):
    monkeypatch.setattr(fichas, "FICHAS_FILE", str(tmp_path / "fichas.json"))


def test_salvar_e_obter(monkeypatch, tmp_path):
    _isolar(monkeypatch, tmp_path)
    ok, msg = fichas.salvar_ficha("Maria", {"nome": "Maria", "cpf": "123"})
    assert ok is True
    assert fichas.obter_ficha("Maria") == {"nome": "Maria", "cpf": "123"}
    assert fichas.listar_fichas() == ["Maria"]


def test_salvar_ignora_vazios(monkeypatch, tmp_path):
    _isolar(monkeypatch, tmp_path)
    fichas.salvar_ficha("X", {"nome": "X", "vazio": "", "nada": "  "})
    assert fichas.obter_ficha("X") == {"nome": "X"}


def test_salvar_sem_dados_rejeita(monkeypatch, tmp_path):
    _isolar(monkeypatch, tmp_path)
    ok, msg = fichas.salvar_ficha("X", {"a": ""})
    assert ok is False
    assert "nenhum campo" in msg.lower()


def test_salvar_nome_vazio_rejeita(monkeypatch, tmp_path):
    _isolar(monkeypatch, tmp_path)
    ok, msg = fichas.salvar_ficha("  ", {"a": "b"})
    assert ok is False


def test_sobrescrever_ficha(monkeypatch, tmp_path):
    _isolar(monkeypatch, tmp_path)
    fichas.salvar_ficha("A", {"nome": "antigo"})
    fichas.salvar_ficha("A", {"nome": "novo"})
    assert fichas.obter_ficha("A") == {"nome": "novo"}
    assert fichas.listar_fichas() == ["A"]


def test_remover_ficha(monkeypatch, tmp_path):
    _isolar(monkeypatch, tmp_path)
    fichas.salvar_ficha("A", {"nome": "x"})
    assert fichas.remover_ficha("A") is True
    assert fichas.obter_ficha("A") is None
    assert fichas.remover_ficha("A") is False


def test_arquivo_corrompido_nao_quebra(monkeypatch, tmp_path):
    _isolar(monkeypatch, tmp_path)
    with open(tmp_path / "fichas.json", "w", encoding="utf-8") as f:
        f.write("{invalido")
    assert fichas.listar_fichas() == []
    assert fichas.obter_ficha("A") is None


def test_formato_do_arquivo(monkeypatch, tmp_path):
    _isolar(monkeypatch, tmp_path)
    fichas.salvar_ficha("B", {"nome": "B"})
    with open(tmp_path / "fichas.json", encoding="utf-8") as f:
        dados = json.load(f)
    assert "atualizado_em" in dados["B"]
    assert dados["B"]["dados"] == {"nome": "B"}
