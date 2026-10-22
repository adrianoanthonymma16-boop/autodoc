"""Página do mapeamento e extração de PDF com várias páginas."""
from PIL import Image

from core.state import AppState
from services import extracao as extracao_mod
from services.extracao import ExtracaoService
from services.mapeamento import MapeamentoService


def test_mapeamento_guarda_pagina_e_sincroniza_lote():
    state = AppState()
    svc = MapeamentoService(state)
    svc.adicionar("NOME", "doc.pdf", "pdf", 10, 20, 50, 60, pagina=2)
    assert state.mapeamento["NOME"]["pagina"] == 2
    assert state.lote_fontes[0]["mapeamento"]["NOME"]["pagina"] == 2


def test_adicionar_confirmado_guarda_pagina():
    state = AppState()
    svc = MapeamentoService(state)
    svc.adicionar_confirmado(
        "CPF", "doc.pdf", "pdf", 1, 2, 3, 4,
        valor="123", confianca=88.0, pagina=1,
    )
    assert state.mapeamento["CPF"]["pagina"] == 1
    assert state.dados_extraidos["CPF"] == "123"


def test_pagina_padrao_zero_para_compatibilidade():
    state = AppState()
    svc = MapeamentoService(state)
    svc.adicionar("X", "doc.pdf", "pdf", 0, 0, 10, 10)
    assert state.mapeamento["X"]["pagina"] == 0


def test_extrair_de_fonte_carrega_pagina_do_mapeamento(monkeypatch):
    state = AppState()
    state.placeholders = ["A"]
    state.lote_fontes = [{
        "documento_path": "x.pdf",
        "documento_tipo": "pdf",
        "mapeamento": {"A": {"x1": 1, "y1": 2, "x2": 3, "y2": 4, "pagina": 2}},
    }]
    chamadas = []

    def fake_pdf(path, pagina=0):
        chamadas.append((path, pagina))
        return Image.new("RGB", (10, 10), "white")

    monkeypatch.setattr(extracao_mod, "pdf_para_imagem", fake_pdf)
    monkeypatch.setattr(
        extracao_mod, "extrair_recorte_com_confianca", lambda img, coords: ("ok", 90.0)
    )
    dados = ExtracaoService(state).extrair_de_fonte(state.lote_fontes[0])
    assert dados == {"A": "ok"}
    assert chamadas == [("x.pdf", 2)]
