"""Geometria de janela: parse e clamp dentro da área visível."""
import pytest

from ui.window_utils import clamp_geometry, parse_geometry


def test_parse_geometry_valida():
    assert parse_geometry("1326x688+20+40") == (1326, 688, 20, 40)
    assert parse_geometry("1326x688-111-10") == (1326, 688, -111, -10)
    assert parse_geometry("1326x688+-257+216") == (1326, 688, -257, 216)


@pytest.mark.parametrize("geo", ["", None, "abc", "1326x688", "1326x688+20"])
def test_parse_geometry_invalida(geo):
    assert parse_geometry(geo) is None


def test_clamp_move_janela_fora_da_tela():
    assert clamp_geometry("1326x688-111+172", 1366, 768) == "1326x688+0+80"
    assert clamp_geometry("1326x688+-257+216", 1366, 768) == "1326x688+0+80"


def test_clamp_reduz_janela_maior_que_tela():
    assert clamp_geometry("2000x1200+0+0", 1366, 768) == "1326x688+0+0"


def test_clamp_respeita_monitor_a_esquerda():
    assert clamp_geometry("1200x700-1500+100", 1920, 1080, -1920, 0) == \
        "1200x700-1500+100"


def test_clamp_limita_margem_negativa_do_monitor():
    assert clamp_geometry("800x600-2500+0", 1920, 1080, -1920, 0) == \
        "1020x640-1920+0"


def test_clamp_tamanho_minimo():
    assert clamp_geometry("400x300+10+10", 1366, 768) == "1020x640+10+10"


def test_clamp_geometria_invalida_retorna_none():
    assert clamp_geometry("nope", 1366, 768) is None
