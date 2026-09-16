"""Tests for MapeamentoService (undo/redo)"""
from core.state import AppState
from services.mapeamento import MapeamentoService


class TestMapeamentoService:
    def _make_service(self):
        state = AppState()
        return MapeamentoService(state), state

    def test_adicionar(self):
        svc, state = self._make_service()
        svc.adicionar("NOME", "test.pdf", "pdf", 10, 20, 100, 50)
        assert "NOME" in state.mapeamento
        assert state.mapeamento["NOME"]["documento_path"] == "test.pdf"
        assert state.mapeamento["NOME"]["x1"] == 10

    def test_remover_placeholder(self):
        svc, state = self._make_service()
        svc.adicionar("NOME", "test.pdf", "pdf", 10, 20, 100, 50)
        svc.remover_placeholder("NOME")
        assert "NOME" not in state.mapeamento

    def test_desfazer_refazer(self):
        svc, state = self._make_service()
        svc.adicionar("NOME", "a.pdf", "pdf", 10, 20, 100, 50)
        assert "NOME" in state.mapeamento

        ok, _ = svc.desfazer()
        assert ok is True
        assert "NOME" not in state.mapeamento

        ok, _ = svc.refazer()
        assert ok is True
        assert "NOME" in state.mapeamento
        assert state.mapeamento["NOME"]["documento_path"] == "a.pdf"

    def test_desfazer_empty(self):
        svc, state = self._make_service()
        ok, msg = svc.desfazer()
        assert ok is False

    def test_refazer_empty(self):
        svc, state = self._make_service()
        ok, msg = svc.refazer()
        assert ok is False

    def test_desfazer_clears_redo(self):
        svc, state = self._make_service()
        svc.adicionar("A", "a.pdf", "pdf", 10, 20, 100, 50)
        svc.desfazer()
        assert len(state.redo_stack) == 1
        svc.adicionar("B", "b.pdf", "pdf", 10, 20, 100, 50)
        assert len(state.redo_stack) == 0

    def test_limpar(self):
        svc, state = self._make_service()
        svc.adicionar("A", "a.pdf", "pdf", 10, 20, 100, 50)
        svc.adicionar("B", "b.pdf", "pdf", 10, 20, 100, 50)
        svc.limpar()
        assert state.mapeamento == {}
        assert state.lote_fontes == []

    def test_sync_lote(self):
        svc, state = self._make_service()
        svc.adicionar("NOME", "doc.pdf", "pdf", 10, 20, 100, 50)
        assert len(state.lote_fontes) == 1
        assert "NOME" in state.lote_fontes[0]["mapeamento"]
