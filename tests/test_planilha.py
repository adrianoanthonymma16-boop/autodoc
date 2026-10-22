"""Testes do serviço de planilha (Fase 4)."""

import pytest

from services.planilha import (
    dados_da_linha,
    ler_planilha,
    normalizar,
    sugerir_mapeamento,
)


def _csv(tmp_path, texto, nome="dados.csv", encoding="utf-8"):
    caminho = tmp_path / nome
    caminho.write_text(texto, encoding=encoding)
    return str(caminho)


def test_normalizar_acentos_e_pontuacao():
    assert normalizar("Nome Completo (mãe)") == "nome completo mae"
    assert normalizar("CPF/CNPJ") == "cpf cnpj"


def test_ler_csv(tmp_path):
    caminho = _csv(tmp_path, "nome,cpf\nMaria,123\nJoao,456\n")
    colunas, linhas = ler_planilha(caminho)
    assert colunas == ["nome", "cpf"]
    assert linhas == [["Maria", "123"], ["Joao", "456"]]


def test_ler_csv_ponto_e_virgula(tmp_path):
    caminho = _csv(tmp_path, "nome;cpf\nMaria;123\n")
    colunas, linhas = ler_planilha(caminho)
    assert colunas == ["nome", "cpf"]
    assert linhas == [["Maria", "123"]]


def test_ler_csv_latin1(tmp_path):
    caminho = _csv(tmp_path, "nome\nJoão\n", encoding="latin-1")
    _, linhas = ler_planilha(caminho)
    assert linhas == [["João"]]


def test_ler_csv_ignora_linhas_vazias(tmp_path):
    caminho = _csv(tmp_path, "nome\nMaria\n\n\nJoao\n")
    _, linhas = ler_planilha(caminho)
    assert linhas == [["Maria"], ["Joao"]]


def test_planilha_vazia(tmp_path):
    caminho = _csv(tmp_path, "\n\n")
    with pytest.raises(ValueError, match="vazia"):
        ler_planilha(caminho)


def test_planilha_sem_dados(tmp_path):
    caminho = _csv(tmp_path, "nome,cpf\n")
    with pytest.raises(ValueError, match="linha de dados"):
        ler_planilha(caminho)


def test_formato_nao_suportado(tmp_path):
    caminho = tmp_path / "x.txt"
    caminho.write_text("a", encoding="utf-8")
    with pytest.raises(ValueError, match="não suportado"):
        ler_planilha(str(caminho))


def test_coluna_vazia_recebe_nome_generico(tmp_path):
    caminho = _csv(tmp_path, "nome,,x\na,b,c\n")
    colunas, _ = ler_planilha(caminho)
    assert colunas == ["nome", "Coluna 2", "x"]


def test_ler_xlsx(tmp_path):
    openpyxl = pytest.importorskip("openpyxl")
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["nome", "cpf"])
    ws.append(["Maria", 123])
    caminho = str(tmp_path / "dados.xlsx")
    wb.save(caminho)
    colunas, linhas = ler_planilha(caminho)
    assert colunas == ["nome", "cpf"]
    assert linhas == [["Maria", "123"]]


def test_sugerir_mapeamento_exato_e_contem():
    sugest = sugerir_mapeamento(["Nome completo", "CPF"], ["nome_completo", "cpf", "cidade"])
    assert sugest == {"nome_completo": "Nome completo", "cpf": "CPF"}
    assert "cidade" not in sugest


def test_sugerir_mapeamento_similaridade():
    sugest = sugerir_mapeamento(["Data de Nascimento"], ["data_nascimento"])
    assert sugest == {"data_nascimento": "Data de Nascimento"}


def test_sugerir_nao_reusa_coluna():
    sugest = sugerir_mapeamento(["nome"], ["nome", "nome_completo"])
    assert sugest.get("nome") == "nome"
    assert "nome_completo" not in sugest


def test_dados_da_linha():
    colunas = ["nome", "cpf", "cidade"]
    linha = ["Maria", "123", "Recife"]
    dados = dados_da_linha(colunas, linha, {"nome": "nome", "cpf": "cpf", "telefone": "telefone"})
    assert dados == {"nome": "Maria", "cpf": "123", "telefone": ""}


def test_dados_da_linha_coluna_inexistente():
    dados = dados_da_linha(["nome"], ["Maria"], {"nome": "nome", "x": "nao_existe"})
    assert dados["x"] == ""


def test_dados_da_linha_linha_curta():
    dados = dados_da_linha(["a", "b"], ["1"], {"a": "a", "b": "b"})
    assert dados == {"a": "1", "b": ""}
