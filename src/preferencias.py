"""
Gerencia preferências do usuário salvas em JSON
"""

import json
import os

PREFS_PATH = os.path.expanduser("~/.autodoc/prefs.json")

DEFAULTS = {
    "tema": "cosmo",
    "tamanho_janela": "1280x820",
    "ultimo_diretorio_modelo": os.path.expanduser("~"),
    "ultimo_diretorio_anexo": os.path.expanduser("~"),
    "ultimo_diretorio_saida": os.path.expanduser("~"),
    "idioma": "pt",
    "confirmacoes_ativadas": True,
}


def carregar_preferencias():
    if not os.path.exists(PREFS_PATH):
        return dict(DEFAULTS)

    try:
        with open(PREFS_PATH, encoding="utf-8") as f:
            data = json.load(f)
        prefs = dict(DEFAULTS)
        prefs.update(data)
        return prefs
    except (OSError, json.JSONDecodeError):
        return dict(DEFAULTS)


def salvar_preferencias(prefs):
    os.makedirs(os.path.dirname(PREFS_PATH), exist_ok=True)
    tmp = PREFS_PATH + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(prefs, f, indent=2, ensure_ascii=False)
        os.replace(tmp, PREFS_PATH)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def get_preferencia(chave):
    prefs = carregar_preferencias()
    return prefs.get(chave, DEFAULTS.get(chave))


def set_preferencia(chave, valor):
    prefs = carregar_preferencias()
    prefs[chave] = valor
    salvar_preferencias(prefs)
