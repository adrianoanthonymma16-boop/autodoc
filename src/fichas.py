"""
Fichas de dados reaproveitáveis (conjuntos nomeados de campo -> valor).
Permite preencher qualquer modelo com dados já usados antes.
"""
import json
import os
from datetime import datetime

from config import PASTA_APP

FICHAS_FILE = os.path.join(PASTA_APP, "fichas.json")


def _carregar() -> dict:
    if not os.path.exists(FICHAS_FILE):
        return {}
    try:
        with open(FICHAS_FILE, encoding="utf-8") as f:
            dados = json.load(f)
        return dados if isinstance(dados, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _salvar(fichas: dict):
    os.makedirs(os.path.dirname(FICHAS_FILE), exist_ok=True)
    tmp = FICHAS_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(fichas, f, indent=2, ensure_ascii=False)
    os.replace(tmp, FICHAS_FILE)


def listar_fichas() -> list[str]:
    return sorted(_carregar().keys(), key=str.casefold)


def salvar_ficha(nome: str, dados: dict) -> tuple[bool, str]:
    """Salva/sobrescreve uma ficha (ignora campos vazios)."""
    nome = (nome or "").strip()
    if not nome:
        return False, "Informe um nome para a ficha."
    limpos = {k: v for k, v in (dados or {}).items() if v and str(v).strip()}
    if not limpos:
        return False, "A ficha não tem nenhum campo preenchido."
    fichas = _carregar()
    fichas[nome] = {
        "dados": limpos,
        "atualizado_em": datetime.now().isoformat(timespec="seconds"),
    }
    _salvar(fichas)
    return True, f"Ficha '{nome}' salva."


def obter_ficha(nome: str) -> dict | None:
    entrada = _carregar().get((nome or "").strip())
    if not entrada:
        return None
    return dict(entrada.get("dados", {}))


def remover_ficha(nome: str) -> bool:
    fichas = _carregar()
    if nome not in fichas:
        return False
    del fichas[nome]
    _salvar(fichas)
    return True
