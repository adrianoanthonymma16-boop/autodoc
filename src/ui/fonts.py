"""Registro de fontes empacotadas com o app (Windows).

Linux/macOS usam fontconfig — basta o pacote fonts-inter instalado.
No Windows a fonte só fica disponível para o processo atual depois de
registrada via GDI, então chamamos isso antes de criar a janela.
"""

from __future__ import annotations

import sys

from resources import asset_path


def register_bundled_fonts() -> int:
    """Registra os .ttf de assets/fonts no processo atual. Retorna quantos."""
    if sys.platform != "win32":
        return 0
    folder = asset_path("fonts")
    if not folder.is_dir():
        return 0

    import ctypes

    total = 0
    for ttf in sorted(folder.glob("*.ttf")):
        if ctypes.windll.gdi32.AddFontResourceExW(str(ttf), 0x10, 0):
            total += 1
    return total
