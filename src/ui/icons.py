"""
Ícones SVG — fonte única de verdade para pictogramas da UI.

Diretriz (AGENTS.md): nenhum emoji colorido na interface; todo pictograma
vem de ``assets/icons/*.svg`` (stroke 24x24) rasterizado aqui via PIL,
sem dependência de sistema (sem cairo) e sem fonte emoji.

Uso:
    from ui.icons import get
    ctk.CTkButton(..., image=get("save", 18, c["text_on_primary"]), text="Salvar")

``render()`` é puro (PIL, sem Tk) e coberto por teste. ``get()`` envolve
em ``CTkImage`` com cache por (nome, tamanho, cor).
"""

import math
import re
import xml.etree.ElementTree as ET
from pathlib import Path

ICON_DIR = Path(__file__).resolve().parent.parent.parent / "assets" / "icons"

ICONS = (
    "doc", "library", "target", "spark", "clock",
    "moon", "sun", "refresh", "save", "search",
    "edit", "rocket", "check", "alert", "folder",
    "inbox", "image", "x", "plus", "minus", "undo",
)

_PIL_CACHE: dict = {}

_TOKEN = re.compile(
    r"[AaCcHhLlMmQqSsTtVvZz]|[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?"
)
_NARGS = {"M": 2, "L": 2, "H": 1, "V": 1, "C": 6, "S": 4,
          "Q": 4, "T": 2, "A": 7, "Z": 0}


def available(name: str) -> bool:
    return name in ICONS and (ICON_DIR / f"{name}.svg").exists()


def _norm_color(value: str | None, fallback: str) -> str | None:
    if value is None:
        return fallback
    v = value.strip()
    if v in ("", "none"):
        return None
    if v == "currentColor":
        return fallback
    return v


def _parse_points(text: str) -> list:
    nums = [float(t) for t in _TOKEN.findall(text or "")
            if not t.isalpha()]
    return [(nums[i], nums[i + 1]) for i in range(0, len(nums) - 1, 2)]


def _cubic(p0, p1, p2, p3, n=16) -> list:
    pts = []
    for i in range(1, n + 1):
        t = i / n
        mt = 1 - t
        pts.append((
            mt**3 * p0[0] + 3 * mt * mt * t * p1[0]
            + 3 * mt * t * t * p2[0] + t**3 * p3[0],
            mt**3 * p0[1] + 3 * mt * mt * t * p1[1]
            + 3 * mt * t * t * p2[1] + t**3 * p3[1],
        ))
    return pts


def _quad(p0, p1, p2, n=12) -> list:
    pts = []
    for i in range(1, n + 1):
        t = i / n
        mt = 1 - t
        pts.append((
            mt * mt * p0[0] + 2 * mt * t * p1[0] + t * t * p2[0],
            mt * mt * p0[1] + 2 * mt * t * p1[1] + t * t * p2[1],
        ))
    return pts


def _arc(p0, rx, ry, rot_deg, large, sweep, p1) -> list:
    """Amostra arco SVG (parametrização endpoint->centro, espec F.6.5)."""
    if rx == 0 or ry == 0 or p0 == p1:
        return [p1]
    phi = math.radians(rot_deg % 360)
    cos_phi, sin_phi = math.cos(phi), math.sin(phi)
    dx, dy = (p0[0] - p1[0]) / 2.0, (p0[1] - p1[1]) / 2.0
    x1p, y1p = cos_phi * dx + sin_phi * dy, -sin_phi * dx + cos_phi * dy
    lam = x1p**2 / rx**2 + y1p**2 / ry**2
    if lam > 1:
        s = math.sqrt(lam)
        rx, ry = rx * s, ry * s
    num = rx**2 * ry**2 - rx**2 * y1p**2 - ry**2 * x1p**2
    den = rx**2 * y1p**2 + ry**2 * x1p**2
    co = math.sqrt(max(0.0, num / den)) if den else 0.0
    if large == sweep:
        co = -co
    cxp, cyp = co * rx * y1p / ry, -co * ry * x1p / rx
    cx = cos_phi * cxp - sin_phi * cyp + (p0[0] + p1[0]) / 2.0
    cy = sin_phi * cxp + cos_phi * cyp + (p0[1] + p1[1]) / 2.0

    def _ang(ux, uy, vx, vy):
        d = math.hypot(ux, uy) * math.hypot(vx, vy)
        c = max(-1.0, min(1.0, (ux * vx + uy * vy) / d)) if d else 1.0
        a = math.acos(c)
        if ux * vy - uy * vx < 0:
            a = -a
        return a

    t1 = _ang(1, 0, (x1p - cxp) / rx, (y1p - cyp) / ry)
    dt = _ang((x1p - cxp) / rx, (y1p - cyp) / ry,
              (-x1p - cxp) / rx, (-y1p - cyp) / ry)
    dt = dt % (2 * math.pi)
    if not sweep:
        dt -= 2 * math.pi
    n = max(8, int(abs(dt) / (math.pi / 24)) + 1)
    pts = []
    for i in range(1, n + 1):
        a = t1 + dt * i / n
        x = cx + rx * math.cos(a) * cos_phi - ry * math.sin(a) * sin_phi
        y = cy + rx * math.cos(a) * sin_phi + ry * math.sin(a) * cos_phi
        pts.append((x, y))
    return pts


def _parse_path(d: str) -> list:
    """Retorna lista de subpaths: (pontos, fechado)."""
    tokens = _TOKEN.findall(d or "")
    subs, cur, start, cmd = [], [], None, None
    cur_pt = (0.0, 0.0)
    last_cubic = None
    last_quad = None
    i = 0

    def _num():
        nonlocal i
        v = float(tokens[i])
        i += 1
        return v

    def _flush():
        nonlocal cur, start
        if len(cur) > 1:
            subs.append((cur, False))
        cur, start = [], None

    while i < len(tokens):
        t = tokens[i]
        if len(t) == 1 and t.isalpha() and t.upper() in _NARGS:
            cmd, i = t.upper(), i + 1
            is_rel = t != cmd
            if cmd == "Z":
                if cur and start is not None:
                    cur.append(start)
                    subs.append((cur, True))
                    cur_pt = start
                cur, start = [], None
                last_cubic = last_quad = None
                continue
        elif cmd is None:
            i += 1
            continue
        else:
            is_rel = False
        if cmd == "M":
            _flush()
            x, y = _num(), _num()
            if is_rel:
                x, y = cur_pt[0] + x, cur_pt[1] + y
            cur, start, cur_pt = [(x, y)], (x, y), (x, y)
            cmd = "L"  # pares seguintes viram lineto
            last_cubic = last_quad = None
        elif cmd == "L":
            x, y = _num(), _num()
            if is_rel:
                x, y = cur_pt[0] + x, cur_pt[1] + y
            cur.append((x, y))
            cur_pt = (x, y)
            last_cubic = last_quad = None
        elif cmd == "H":
            x = _num()
            if is_rel:
                x = cur_pt[0] + x
            cur.append((x, cur_pt[1]))
            cur_pt = (x, cur_pt[1])
            last_cubic = last_quad = None
        elif cmd == "V":
            y = _num()
            if is_rel:
                y = cur_pt[1] + y
            cur.append((cur_pt[0], y))
            cur_pt = (cur_pt[0], y)
            last_cubic = last_quad = None
        elif cmd == "C":
            pts = [_num() for _ in range(6)]
            p1 = (pts[0], pts[1]) if not is_rel else (cur_pt[0] + pts[0], cur_pt[1] + pts[1])
            p2 = (pts[2], pts[3]) if not is_rel else (cur_pt[0] + pts[2], cur_pt[1] + pts[3])
            p3 = (pts[4], pts[5]) if not is_rel else (cur_pt[0] + pts[4], cur_pt[1] + pts[5])
            cur.extend(_cubic(cur_pt, p1, p2, p3))
            last_cubic, last_quad = (p1, p2), None
            cur_pt = p3
        elif cmd == "S":
            pts = [_num() for _ in range(4)]
            if last_cubic is not None:
                p1 = (2 * cur_pt[0] - last_cubic[1][0],
                      2 * cur_pt[1] - last_cubic[1][1])
            else:
                p1 = cur_pt
            p2 = (pts[0], pts[1]) if not is_rel else (cur_pt[0] + pts[0], cur_pt[1] + pts[1])
            p3 = (pts[2], pts[3]) if not is_rel else (cur_pt[0] + pts[2], cur_pt[1] + pts[3])
            cur.extend(_cubic(cur_pt, p1, p2, p3))
            last_cubic, last_quad = (p1, p2), None
            cur_pt = p3
        elif cmd == "Q":
            pts = [_num() for _ in range(4)]
            p1 = (pts[0], pts[1]) if not is_rel else (cur_pt[0] + pts[0], cur_pt[1] + pts[1])
            p2 = (pts[2], pts[3]) if not is_rel else (cur_pt[0] + pts[2], cur_pt[1] + pts[3])
            cur.extend(_quad(cur_pt, p1, p2))
            last_quad, last_cubic = p1, None
            cur_pt = p2
        elif cmd == "T":
            x, y = _num(), _num()
            if is_rel:
                x, y = cur_pt[0] + x, cur_pt[1] + y
            p1 = (2 * cur_pt[0] - last_quad[0], 2 * cur_pt[1] - last_quad[1]) if last_quad else cur_pt
            cur.extend(_quad(cur_pt, p1, (x, y)))
            last_quad, last_cubic = p1, None
            cur_pt = (x, y)
        elif cmd == "A":
            vals = [_num() for _ in range(7)]
            rx, ry, rot, large, sweep = vals[0], vals[1], vals[2], int(vals[3]), int(vals[4])
            p1 = (vals[5], vals[6]) if not is_rel else (cur_pt[0] + vals[5], cur_pt[1] + vals[6])
            seg = _arc(cur_pt, rx, ry, rot, large, sweep, p1)
            cur.extend(seg)
            cur_pt = p1
            last_cubic = last_quad = None
        else:
            i += 1
    _flush()
    return subs


def _shapes(root, base: dict) -> list:
    """Extrai (kind, geom, stroke, fill, stroke_width)."""
    out = []
    for el in root.iter():
        tag = el.tag.split("}")[-1]
        if tag == "svg":
            continue
        a = dict(base)
        for k in ("stroke", "fill", "stroke-width"):
            if el.get(k) is not None:
                a[k] = el.get(k)
        sw = float(a.get("stroke-width", 2))
        stroke = _norm_color(a.get("stroke"), base["_color"])
        fill = _norm_color(a.get("fill"), base["_color"])
        if tag == "path":
            for pts, closed in _parse_path(el.get("d", "")):
                out.append(("poly", pts, closed, stroke, fill, sw))
        elif tag == "line":
            p = [(float(el.get("x1", 0)), float(el.get("y1", 0))),
                 (float(el.get("x2", 0)), float(el.get("y2", 0)))]
            out.append(("poly", p, False, stroke, fill, sw))
        elif tag in ("polyline", "polygon"):
            pts = _parse_points(el.get("points", ""))
            out.append(("poly", pts, tag == "polygon", stroke, fill, sw))
        elif tag == "rect":
            x, y = float(el.get("x", 0)), float(el.get("y", 0))
            w, h = float(el.get("width", 0)), float(el.get("height", 0))
            rx = float(el.get("rx", 0))
            out.append(("rect", (x, y, w, h, rx), False, stroke, fill, sw))
        elif tag == "circle":
            out.append(("circle",
                        (float(el.get("cx", 0)), float(el.get("cy", 0)),
                         float(el.get("r", 0))), False, stroke, fill, sw))
        elif tag == "ellipse":
            out.append(("ellipse",
                        (float(el.get("cx", 0)), float(el.get("cy", 0)),
                         float(el.get("rx", 0)), float(el.get("ry", 0))),
                        False, stroke, fill, sw))
    return out


def render(name: str, size: int = 18, color: str = "#000000"):
    """Rasteriza o SVG para PIL.Image RGBA (size x size). Puro, sem Tk."""
    from PIL import Image, ImageDraw

    key = (name, int(size), color)
    if key in _PIL_CACHE:
        return _PIL_CACHE[key]
    if not available(name):
        raise ValueError(f"icone desconhecido: {name!r}")

    root = ET.parse(ICON_DIR / f"{name}.svg").getroot()
    vb = [float(t) for t in re.findall(r"[-+]?\d*\.?\d+", root.get("viewBox", "0 0 24 24"))]
    _, _, vb_w, vb_h = (vb + [0, 0, 24, 24])[:4]
    base = {
        "stroke": root.get("stroke", "currentColor"),
        "fill": root.get("fill", "none"),
        "stroke-width": root.get("stroke-width", 2),
        "_color": color,
    }
    shapes = _shapes(root, base)

    ss = 4  # supersampling p/ bordas suaves
    sw_target = max(1.4, float(base["stroke-width"]))
    pad = sw_target / 2 + 1.0
    big = int(size * ss)
    img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    dr = ImageDraw.Draw(img)
    sc = (size - 2 * pad) / max(vb_w, vb_h) * ss

    def _px(pt):
        return (pad * ss + pt[0] * sc, pad * ss + pt[1] * sc)

    for kind, geom, closed, stroke, fill, sw in shapes:
        w = max(1, int(round(sw * sc)))
        if kind == "poly":
            pts = [_px(p) for p in geom]
            if fill and closed and len(pts) > 2:
                dr.polygon(pts, fill=fill)
            if stroke and len(pts) > 1:
                dr.line(pts, fill=stroke, width=w, joint="curve")
                r = w / 2
                for p in (pts[0], pts[-1]):
                    dr.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=stroke)
        elif kind == "rect":
            x, y, w_, h_, rx = geom
            box = [_px((x, y)), _px((x + w_, y + h_))]
            if rx > 0:
                dr.rounded_rectangle(box, radius=rx * sc,
                                     fill=fill, outline=stroke, width=w)
            else:
                dr.rectangle(box, fill=fill, outline=stroke, width=w)
        elif kind == "circle":
            cx, cy, r = geom
            box = [_px((cx - r, cy - r)), _px((cx + r, cy + r))]
            dr.ellipse(box, fill=fill, outline=stroke, width=w)
        elif kind == "ellipse":
            cx, cy, rx, ry = geom
            box = [_px((cx - rx, cy - ry)), _px((cx + rx, cy + ry))]
            dr.ellipse(box, fill=fill, outline=stroke, width=w)

    img = img.resize((int(size), int(size)), Image.LANCZOS)
    _PIL_CACHE[key] = img
    return img


_CTK_CACHE: dict = {}


def get(name: str, size: int = 18, color: str = "#000000"):
    """Retorna CTkImage cacheado (requer Tk ativo)."""
    import customtkinter as ctk

    key = (name, int(size), color)
    if key not in _CTK_CACHE:
        pil = render(name, int(size), color)
        _CTK_CACHE[key] = ctk.CTkImage(light_image=pil, dark_image=pil,
                                       size=(int(size), int(size)))
    return _CTK_CACHE[key]


def clear_cache() -> None:
    _PIL_CACHE.clear()
    _CTK_CACHE.clear()
