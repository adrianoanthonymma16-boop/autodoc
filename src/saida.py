"""
Padrões de nome e organização dos documentos gerados.

Tokens de nome (chave simples): {modelo} {data} {hora} {indice}
Placeholders do documento: {{campo}} — substituídos pelos dados preenchidos.
"""
import os
import re
from datetime import datetime

PADRAO_PADRAO = "{modelo}"
SUFIXO_MAX = 120

_INVALIDOS = re.compile(r'[\\/:*?"<>|\x00-\x1f]')
_PLACEHOLDER = re.compile(r"\{\{\s*([^}]+?)\s*\}\}")
_TOKEN = re.compile(r"\{(modelo|data|hora|indice)\}")


def sanitizar_nome(nome: str) -> str:
    """Remove caracteres inválidos para nome de arquivo (Linux/Windows)."""
    nome = _INVALIDOS.sub("_", str(nome or ""))
    nome = re.sub(r"\s+", " ", nome).strip(" .")
    return nome[:SUFIXO_MAX] or "documento"


def renderizar_nome(padrao: str, modelo_path: str, dados: dict | None = None,
                    indice: int | None = None, momento: datetime | None = None) -> str:
    """Aplica tokens e placeholders ao padrão, devolvendo um nome sanitizado."""
    dados = dados or {}
    momento = momento or datetime.now()
    modelo = os.path.splitext(os.path.basename(modelo_path or ""))[0] or "documento"

    base = (padrao or PADRAO_PADRAO)

    def _substituir_placeholder(match):
        campo = match.group(1).strip()
        valor = dados.get(campo, "")
        return sanitizar_nome(valor) if valor != "" else ""

    base = _PLACEHOLDER.sub(_substituir_placeholder, base)

    ctx = {
        "modelo": modelo,
        "data": momento.strftime("%Y-%m-%d"),
        "hora": momento.strftime("%H%M"),
        "indice": str(indice) if indice is not None else "",
    }
    base = _TOKEN.sub(lambda m: ctx[m.group(1)], base)
    return sanitizar_nome(base)


def _unico(caminho: str) -> str:
    """Evita sobrescrever: adiciona _2, _3... se o arquivo já existir."""
    if not os.path.exists(caminho):
        return caminho
    raiz, ext = os.path.splitext(caminho)
    contador = 2
    while os.path.exists(f"{raiz}_{contador}{ext}"):
        contador += 1
    return f"{raiz}_{contador}{ext}"


def caminho_saida(pasta: str, padrao: str, modelo_path: str, dados: dict | None = None,
                  extensao: str = "", indice: int | None = None,
                  organizar_por_data: bool = False,
                  momento: datetime | None = None, evitar_sobrescrita: bool = True) -> str:
    """Monta o caminho final respeitando pasta, padrão e subpasta por data."""
    momento = momento or datetime.now()
    destino = pasta
    if organizar_por_data:
        destino = os.path.join(pasta, momento.strftime("%Y-%m-%d"))
    os.makedirs(destino, exist_ok=True)
    nome = renderizar_nome(padrao, modelo_path, dados, indice=indice, momento=momento)
    ext = extensao if extensao.startswith(".") or not extensao else f".{extensao}"
    caminho = os.path.join(destino, f"{nome}{ext}")
    return _unico(caminho) if evitar_sobrescrita else caminho
