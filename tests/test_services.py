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
from services.extracao import ExtracaoService


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

    @patch("services.modelo.extrair_placeholders_docx", return_value={"X"})
    @patch("services.modelo.docx_suportado", return_value=True)
    def test_adicionar_ao_lote_docx(self, mock_sup, mock_ext, state):
        svc = ModeloService(state)
        with patch("services.modelo.validar_extensao", return_value=(True, ".docx", "ok")):
            ok, msg = svc.adicionar_ao_lote("/tmp/model.docx")
        assert ok is True
        assert len(state.modelos) == 1
        assert state.modelos[0]["tipo"] == "docx"
        assert state.modelos[0]["placeholders"] == ["X"]

    @patch("services.modelo.extrair_placeholders_docx", return_value={"X"})
    @patch("services.modelo.docx_suportado", return_value=False)
    def test_adicionar_ao_lote_docx_nao_suportado(self, mock_sup, mock_ext, state):
        svc = ModeloService(state)
        with patch("services.modelo.validar_extensao", return_value=(True, ".docx", "ok")):
            ok, msg = svc.adicionar_ao_lote("/tmp/model.docx")
        assert ok is False
        assert "DOCX" in msg

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


# --- ExtracaoService: callbacks marshallizados (thread-safe Tk) ---

class TestExtracaoServiceCallbacks:
    def _state_mapeado(self):
        state = AppState()
        state.placeholders = ["PH1", "PH2"]
        state.mapeamento["PH1"] = {
            "documento_path": "/tmp/a.png",
            "documento_tipo": "imagem",
            "x1": 0, "y1": 0, "x2": 10, "y2": 10,
        }
        return state

    @patch("services.extracao.extrair_texto_do_recorte", return_value="TEXTO")
    @patch("services.extracao.Image.open")
    def test_callbacks_marshallizados_apenas_mapeados(self, mock_open, mock_ocr):
        from services.extracao import ExtracaoService
        svc = ExtracaoService(self._state_mapeado())
        # marshal simula after(0, fn): agenda e devolve; main loop depois executa
        agenda = []
        def marshal(fn):
            agenda.append(fn)
            return fn
        on_prog = MagicMock()
        on_done = MagicMock()
        on_err = MagicMock()

        thread = svc.extrair_todos(on_progress=on_prog, on_done=on_done, on_error=on_err, marshal=marshal)
        thread.join(timeout=5)

        # nenhum callback toca Tk fora da main thread: tudo foi agendado
        assert on_prog.call_count == 0
        assert on_err.call_count == 0
        # on_done continua sendo agendado pelo caller na view (não no serviço)
        on_done.assert_called_once()
        dados = on_done.call_args[0][0]
        assert dados["PH1"] == "TEXTO"
        assert dados["PH2"] == ""  # não mapeado fica vazio
        # executa a fila agendada (simulando a main thread)
        for fn in agenda:
            fn()
        assert on_prog.call_count == 2  # PH1 e PH2
        assert on_err.call_count == 0

    @patch("services.extracao.extrair_texto_do_recorte", side_effect=RuntimeError("ocr fail"))
    def test_on_error_marshallizado(self, mock_ocr):
        from services.extracao import ExtracaoService
        svc = ExtracaoService(self._state_mapeado())
        agenda = []
        def marshal(fn):
            agenda.append(fn)
            return fn
        on_err = MagicMock()
        svc.extrair_todos(on_error=on_err, marshal=marshal).join(timeout=5)
        assert on_err.call_count == 0  # não chamado direto no worker
        for fn in agenda:
            fn()
        assert on_err.call_count == 1
