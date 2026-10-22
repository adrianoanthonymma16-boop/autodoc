"""Testes de padrão de nome e organização da saída (Fase 2)."""
import os
from datetime import datetime

from saida import caminho_saida, renderizar_nome, sanitizar_nome


MOMENTO = datetime(2026, 10, 21, 14, 35)


def test_padrao_padrao_usa_nome_do_modelo():
    assert renderizar_nome("", "/tmp/Contrato DIEX.odt") == "Contrato DIEX"


def test_tokens_data_hora_indice():
    nome = renderizar_nome("{modelo}_{data}_{hora}_{indice}", "/tmp/Ofício.docx",
                           indice=3, momento=MOMENTO)
    assert nome == "Ofício_2026-10-21_1435_3"


def test_placeholder_preenche_valor():
    nome = renderizar_nome("{{nome}}_{modelo}", "/tmp/ficha.odt",
                           dados={"nome": "Maria Silva"}, momento=MOMENTO)
    assert nome == "Maria Silva_ficha"


def test_placeholder_vazio_desaparece():
    nome = renderizar_nome("{{nome}}_{modelo}", "/tmp/ficha.odt", dados={}, momento=MOMENTO)
    assert nome == "_ficha"


def test_sanitiza_caracteres_invalidos():
    assert sanitizar_nome('a/b:c*d?"e"<f>|g') == "a_b_c_d__e__f__g"


def test_sanitiza_espacos_e_pontos():
    assert sanitizar_nome("  nome...  ") == "nome"
    assert sanitizar_nome("") == "documento"


def test_caminho_com_extensao_e_pasta(tmp_path):
    caminho = caminho_saida(str(tmp_path), "{modelo}", "/tmp/ata.odt", extensao=".odt", momento=MOMENTO)
    assert caminho == os.path.join(str(tmp_path), "ata.odt")


def test_caminho_subpasta_por_data(tmp_path):
    caminho = caminho_saida(str(tmp_path), "{modelo}", "/tmp/ata.odt",
                            extensao=".odt", organizar_por_data=True, momento=MOMENTO)
    assert caminho == os.path.join(str(tmp_path), "2026-10-21", "ata.odt")
    assert os.path.isdir(os.path.join(str(tmp_path), "2026-10-21"))


def test_caminho_nao_sobrescreve(tmp_path):
    primeiro = caminho_saida(str(tmp_path), "{modelo}", "/tmp/ata.odt", extensao=".odt", momento=MOMENTO)
    open(primeiro, "w").close()
    segundo = caminho_saida(str(tmp_path), "{modelo}", "/tmp/ata.odt", extensao=".odt", momento=MOMENTO)
    assert segundo.endswith("ata_2.odt")


def test_extensao_sem_ponto(tmp_path):
    caminho = caminho_saida(str(tmp_path), "{modelo}", "/tmp/ata.odt", extensao="odt", momento=MOMENTO)
    assert caminho.endswith(".odt")


def test_token_desconhecido_fica_intacto():
    assert renderizar_nome("{desconhecido}", "/tmp/a.odt") == "{desconhecido}"
