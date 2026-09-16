"""Tests for services layer"""
import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock
from PIL import Image

from core.state import AppState
from services.documento import DocumentoService
from services.geracao import GeracaoService
from services.modelo import ModeloService
from services.mapeamento import MapeamentoService


@pytest.fixture
def state():
    return AppState()


@pytest.fixture
def tmp_png():
    """Create a temporary PNG file"""
    img = Image.new("RGB", (100, 100), color="white")
    path = os.path.join(tempfile.gettempdir(), "test_doc.png")
    img.save(path, "PNG")
    yield path
    if os.path.exists(path):
        os.remove(path)


# --- DocumentoService ---

class TestDocumentoService:
    def test_anexar_imagem(self, state, tmp_png):
        svc = DocumentoService(state)
        ok, msg = svc.anexar(tmp_png)
        assert ok is True
        assert len(state.documentos_anexados) == 1
        assert state.documentos_anexados[0]["tipo"] == "imagem"

    def test_anexar_duplicado(self, state, tmp_png):
        svc = DocumentoService(state)
        svc.anexar(tmp_png)
        ok, msg = svc.anexar(tmp_png)
        assert ok is False
        assert "já anexado" in msg.lower()

    def test_anexar_extensao_invalida(self, state):
        svc = DocumentoService(state)
        ok, msg = svc.anexar("/tmp/test.txt")
        assert ok is False

    def test_remover_por_path(self, state, tmp_png):
        svc = DocumentoService(state)
        svc.anexar(tmp_png)
        assert len(state.documentos_anexados) == 1
        result = svc.remover_por_path(tmp_png)
        assert result is True
        assert len(state.documentos_anexados) == 0

    def test_remover_inexistente(self, state, tmp_png):
        svc = DocumentoService(state)
        result = svc.remover_por_path(tmp_png)
        assert result is False

    def test_selecionar(self, state, tmp_png):
        svc = DocumentoService(state)
        svc.anexar(tmp_png)
        doc = svc.selecionar(tmp_png)
        assert doc is not None
        assert state.documento_atual_path == tmp_png
        assert state.documento_tipo == "imagem"

    def test_selecionar_inexistente(self, state):
        svc = DocumentoService(state)
        doc = svc.selecionar("/nonexistent.png")
        assert doc is None

    def test_remover_limpa_mapeamento(self, state, tmp_png):
        svc = DocumentoService(state)
        svc.anexar(tmp_png)
        state.mapeamento["PH1"] = {"documento_path": tmp_png}
        svc.remover_por_path(tmp_png)
        assert "PH1" not in state.mapeamento


# --- GeracaoService ---

class TestGeracaoService:
    def test_gerar_um_tipo_desconhecido(self, state):
        svc = GeracaoService(state)
        with pytest.raises(Exception, match="desconhecido"):
            svc.gerar_um("model.xyz", "xyz", {}, "out.xyz")

    @patch("services.geracao.gerar_odt_preenchido")
    def test_gerar_um_odt(self, mock_odt, state):
        svc = GeracaoService(state)
        svc.gerar_um("model.odt", "odt", {"PH": "val"}, "out.odt")
        mock_odt.assert_called_once_with("model.odt", {"PH": "val"}, "out.odt")

    @patch("services.geracao.gerar_docx_preenchido")
    @patch("services.geracao.docx_suportado", return_value=True)
    def test_gerar_um_docx(self, mock_sup, mock_docx, state):
        svc = GeracaoService(state)
        svc.gerar_um("model.docx", "docx", {"PH": "val"}, "out.docx")
        mock_docx.assert_called_once_with("model.docx", {"PH": "val"}, "out.docx")

    @patch("services.geracao.docx_suportado", return_value=False)
    def test_gerar_docx_nao_suportado(self, mock_sup, state):
        svc = GeracaoService(state)
        with pytest.raises(Exception, match="não suportado"):
            svc.gerar_um("model.docx", "docx", {}, "out.docx")


# --- ModeloService ---

class TestModeloService:
    def test_remover_do_lote(self, state):
        svc = ModeloService(state)
        state.modelos = [
            {"path": "a.odt", "tipo": "odt", "placeholders": ["A"]},
            {"path": "b.odt", "tipo": "odt", "placeholders": ["B"]},
        ]
        svc.remover_do_lote(0)
        assert len(state.modelos) == 1
        assert state.modelo_path == "b.odt"

    def test_remover_do_lote_ultimo(self, state):
        svc = ModeloService(state)
        state.modelos = [{"path": "a.odt", "tipo": "odt", "placeholders": ["A"]}]
        svc.remover_do_lote(0)
        assert state.modelos == []
        assert state.modelo_path is None
        assert state.placeholders == []

    def test_remover_do_lote_indice_invalido(self, state):
        svc = ModeloService(state)
        state.modelos = [{"path": "a.odt", "tipo": "odt", "placeholders": ["A"]}]
        svc.remover_do_lote(5)
        assert len(state.modelos) == 1

    def test_usar_da_biblioteca(self, state):
        svc = ModeloService(state)
        svc.usar_da_biblioteca("model.odt", "odt", ["PH1", "PH2"])
        assert state.modelo_path == "model.odt"
        assert state.modelo_tipo == "odt"
        assert state.placeholders == ["PH1", "PH2"]

    @patch("services.modelo.extrair_placeholders_odt", return_value={"A", "B"})
    def test_carregar_arquivo_unico_odt(self, mock_ext, state):
        svc = ModeloService(state)
        with patch("services.modelo.validar_extensao", return_value=(True, ".odt", "ok")):
            ok, msg = svc.carregar_arquivo_unico("/tmp/model.odt")
        assert ok is True
        assert state.modelo_tipo == "odt"
        assert set(state.placeholders) == {"A", "B"}

    @patch("services.modelo.extrair_placeholders_odt", return_value=set())
    def test_carregar_sem_placeholders(self, mock_ext, state):
        svc = ModeloService(state)
        with patch("services.modelo.validar_extensao", return_value=(True, ".odt", "ok")):
            ok, msg = svc.carregar_arquivo_unico("/tmp/empty.odt")
        assert ok is False
        assert "Nenhum placeholder" in msg

    def test_carregar_extensao_invalida(self, state):
        svc = ModeloService(state)
        with patch("services.modelo.validar_extensao", return_value=(False, ".pdf", "não suportado")):
            ok, msg = svc.carregar_arquivo_unico("/tmp/doc.pdf")
        assert ok is False

    @patch("services.modelo.extrair_placeholders_odt", return_value={"X"})
    def test_adicionar_ao_lote(self, mock_ext, state):
        svc = ModeloService(state)
        with patch("services.modelo.validar_extensao", return_value=(True, ".odt", "ok")):
            ok, msg = svc.adicionar_ao_lote("/tmp/model.odt")
        assert ok is True
        assert len(state.modelos) == 1
        assert state.modelos[0]["placeholders"] == ["X"]

    @patch("services.modelo.extrair_placeholders_odt", return_value={"X"})
    def test_adicionar_ao_lote_duplicado(self, mock_ext, state):
        svc = ModeloService(state)
        state.modelos = [{"path": "/tmp/model.odt", "tipo": "odt", "placeholders": ["X"]}]
        with patch("services.modelo.validar_extensao", return_value=(True, ".odt", "ok")):
            ok, msg = svc.adicionar_ao_lote("/tmp/model.odt")
        assert ok is False
        assert "já anexado" in msg.lower()


# --- MapeamentoService extras ---

class TestMapeamentoServiceExtras:
    def test_exportar_importar(self, state, tmp_path):
        svc = MapeamentoService(state)
        svc.adicionar("PH1", "doc.pdf", "pdf", 10, 20, 100, 50)
        export_path = str(tmp_path / "export.json")
        svc.exportar(export_path)
        assert os.path.exists(export_path)

        # Import into fresh state
        state2 = AppState()
        svc2 = MapeamentoService(state2)
        svc2.importar(export_path)
        assert "PH1" in state2.mapeamento
        assert state2.mapeamento["PH1"]["documento_path"] == "doc.pdf"

    def test_backup_atomico(self, state):
        svc = MapeamentoService(state)
        svc.adicionar("PH1", "doc.pdf", "pdf", 10, 20, 100, 50)
        state.modelo_path = "model.odt"
        svc.backup()
        data = svc.restaurar_backup()
        assert data is not None
        assert "PH1" in data["mapeamento"]
