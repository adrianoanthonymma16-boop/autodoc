"""Sequência de campos percorrida pela janela de seleção."""
from ui.views.mapeamento_view import sequencia_pendente


def test_atual_primeiro_e_pendentes_na_ordem():
    phs = ["A", "B", "C", "D"]
    assert sequencia_pendente(phs, {"B": {}}, "C") == ["C", "A", "D"]


def test_sem_atual_retorna_apenas_pendentes():
    assert sequencia_pendente(["A", "B", "C"], {"A": {}}, None) == ["B", "C"]


def test_atual_ja_mapeado_entra_para_remapear():
    assert sequencia_pendente(["A", "B"], {"A": {}, "B": {}}, "A") == ["A"]


def test_todos_mapeados_retorna_so_o_atual():
    phs = ["A", "B"]
    assert sequencia_pendente(phs, {"A": {}, "B": {}}, "B") == ["B"]
