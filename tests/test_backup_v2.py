"""Testes do backup v2 (dados_extraidos + schema)."""
import json
import os

from core.state import AppState
from services.mapeamento import MapeamentoService


def _svc(monkeypatch, tmp_path):
    monkeypatch.setattr("services.mapeamento.BACKUP_FILE", str(tmp_path / "backup.json"))
    state = AppState()
    svc = MapeamentoService(state)
    # backup() só escreve quando existe mapeamento + modelo (guard legado)
    state.modelo_path = "/tmp/modelo.odt"
    state.modelo_tipo = "odt"
    state.mapeamento = {"ph": {"documento_path": "x", "documento_tipo": "imagem", "x1": 0, "y1": 0, "x2": 1, "y2": 1}}
    return state, svc


def test_backup_v2_inclui_dados_extraidos(monkeypatch, tmp_path):
    state, svc = _svc(monkeypatch, tmp_path)
    state.dados_extraidos = {"nome": "Maria"}
    state.confianca_ocr = {"nome": 92.0}
    svc.backup()
    with open(os.path.join(tmp_path, "backup.json"), encoding="utf-8") as f:
        data = json.load(f)
    assert data["schema"] == 2
    assert data["dados_extraidos"] == {"nome": "Maria"}
    assert data["confianca_ocr"] == {"nome": 92.0}


def test_aplicar_backup_restaura_dados_extraidos(monkeypatch, tmp_path):
    state, svc = _svc(monkeypatch, tmp_path)
    svc.aplicar_backup({"mapeamento": {}, "schema": 2, "dados_extraidos": {"nome": "Joao"}})
    assert state.dados_extraidos == {"nome": "Joao"}


def test_aplicar_backup_v1_sem_dados_extraidos(monkeypatch, tmp_path):
    """Backup do schema antigo (v1) aplica sem erro e mantem dados vazios."""
    state, svc = _svc(monkeypatch, tmp_path)
    svc.aplicar_backup({"mapeamento": {"ph": {"documento_path": "x", "documento_tipo": "imagem", "x1": 0, "y1": 0, "x2": 1, "y2": 1}}})
    assert state.dados_extraidos == {}
    assert "ph" in state.mapeamento


def test_restaurar_backup_v2(monkeypatch, tmp_path):
    state, svc = _svc(monkeypatch, tmp_path)
    state.dados_extraidos = {"a": "b"}
    svc.backup()
    data = svc.restaurar_backup()
    assert data is not None
    assert data["schema"] == 2
    assert data["dados_extraidos"] == {"a": "b"}


def test_backup_v2_sem_dados_nao_cabra_nada(monkeypatch, tmp_path):
    """Mesmo sem dados_extraidos, schema vai como 2."""
    _state, svc = _svc(monkeypatch, tmp_path)
    svc.backup()
    with open(os.path.join(tmp_path, "backup.json"), encoding="utf-8") as f:
        data = json.load(f)
    assert data["schema"] == 2
    assert data["dados_extraidos"] == {}
