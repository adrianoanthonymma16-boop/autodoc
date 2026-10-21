"""
Resolução de caminhos de recursos (ícones, fontes, licença).

Funciona tanto rodando do código-fonte quanto congelado por PyInstaller.
"""

import sys
from pathlib import Path


def app_root() -> Path:
    """Raiz dos recursos: diretório do executável quando congelado."""
    frozen = getattr(sys, "_MEIPASS", None)
    if frozen:
        return Path(frozen)
    return Path(__file__).resolve().parent.parent


def resource_path(*parts: str) -> Path:
    return app_root().joinpath(*parts)


def asset_path(*parts: str) -> Path:
    return resource_path("assets", *parts)
