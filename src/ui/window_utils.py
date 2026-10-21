"""Utilitários de geometria de janela (puros, testáveis sem Tk)."""
import re

_GEOM = re.compile(r"^(\d+)x(\d+)([+-]-?\d+)([+-]-?\d+)$")


def _to_int(value):
    # Tk emite coordenadas negativas como "+-257"; int() não aceita esse sinal duplo.
    return int(value.replace("+", "", 1))


def parse_geometry(geo):
    """Converte 'WxH+X+Y' em (w, h, x, y) ou None se inválido."""
    m = _GEOM.match((geo or "").strip())
    if not m:
        return None
    w, h = int(m.group(1)), int(m.group(2))
    return w, h, _to_int(m.group(3)), _to_int(m.group(4))


def clamp_geometry(geo, screen_w, screen_h, screen_x=0, screen_y=0,
                   min_w=1020, min_h=640, margin_w=40, margin_h=80):
    """Mantém a janela dentro da área visível, respeitando um tamanho mínimo.

    Aceita coordenadas negativas (monitor à esquerda/ acima) via screen_x/y.
    Retorna None quando a string não é uma geometria válida.
    """
    parsed = parse_geometry(geo)
    if not parsed:
        return None
    w, h, x, y = parsed
    max_w = max(min_w, screen_w - margin_w)
    max_h = max(min_h, screen_h - margin_h)
    w = min(max(w, min_w), max_w)
    h = min(max(h, min_h), max_h)
    max_x = screen_x + max(0, screen_w - w)
    max_y = screen_y + max(0, screen_h - h)
    x = min(max(x, screen_x), max_x)
    y = min(max(y, screen_y), max_y)
    def sign(v):
        return f"+{v}" if v >= 0 else str(v)

    return f"{w}x{h}{sign(x)}{sign(y)}"
