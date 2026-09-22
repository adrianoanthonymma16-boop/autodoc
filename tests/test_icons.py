"""Ícones SVG: raster, registro e regressão anti-emoji (AGENTS.md §1)."""
import pathlib
import re

import pytest

from ui.icons import ICON_DIR, ICONS, available, clear_cache, get, render

# Pictogramas coloridos, dingbats, setas especiais, VS16 e fullwidth.
# Exceção narrow: U+2713 (✓) como prefixo de status em texto.
_EMOJI = re.compile(
    "[\U0001F000-\U0001FAFF\u2600-\u26FF\u2700-\u27BF"
    "\u2B00-\u2BFF\uFE0F\uFF00-\uFFEF]"
)
_ALLOW = {"\u2713"}
_SCOPE = list((pathlib.Path(__file__).parent.parent / "src" / "ui").rglob("*.py")) + [
    pathlib.Path(__file__).parent.parent / "src" / "mensagens.py",
]


def _coverage(img):
    h = img.split()[3].histogram()
    opaque = sum(h[21:])
    return opaque / (img.size[0] * img.size[1])


def test_registry_completo():
    assert len(ICONS) >= 20
    for name in ICONS:
        assert available(name), name
        assert (ICON_DIR / f"{name}.svg").exists()


def test_render_tamanhos_e_cobertura():
    clear_cache()
    for name in ICONS:
        for size in (16, 24, 44):
            img = render(name, size, "#047857")
            assert img.size == (size, size)
            assert img.mode == "RGBA"
            assert _coverage(img) > 0.005, name


def test_render_cache():
    clear_cache()
    assert render("doc", 18, "#000000") is render("doc", 18, "#000000")
    assert render("doc", 18, "#000000") is not render("doc", 18, "#FFFFFF")


def test_render_icone_desconhecido():
    with pytest.raises(ValueError):
        render("nao-existe", 18, "#000000")


def test_sem_emoji_na_ui_nova():
    bad = []
    for p in _SCOPE:
        for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            hits = [c for c in _EMOJI.findall(line) if c not in _ALLOW]
            if hits:
                bad.append(f"{p.name}:{i} {hits}")
    assert not bad, "emoji/fullwidth em src/ui ou mensagens.py: " + "; ".join(bad)


def test_get_retorna_ctkimage():
    # smoke opcional com display; pula sem Tk
    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
    except Exception:
        pytest.skip("sem display")
    try:
        import customtkinter as ctk
        img = get("doc", 18, "#047857")
        assert isinstance(img, ctk.CTkImage)
        assert get("doc", 18, "#047857") is img
    finally:
        root.destroy()
