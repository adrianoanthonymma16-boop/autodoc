"""Garante que falha ao acessar header/footer nao derruba a leitura do DOCX."""
from modelo_docx import _partes_cabecalho_rodape


class _SecaoComErro:
    @property
    def header(self):
        raise FileNotFoundError("default-header.xml")

    @property
    def footer(self):
        raise FileNotFoundError("default-footer.xml")


class _SecaoOk:
    header = "HDR"
    footer = "FTR"


def test_falha_em_header_nao_propaga():
    assert _partes_cabecalho_rodape(_SecaoComErro()) == []


def test_retorna_header_e_footer_quando_ok():
    assert _partes_cabecalho_rodape(_SecaoOk()) == ["HDR", "FTR"]
