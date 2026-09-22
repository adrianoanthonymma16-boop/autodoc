"""
Widgets reutilizáveis premium
"""
import customtkinter as ctk

from ui.theme import FONTS, get_colors


def card(parent, **kwargs):
    c = get_colors()
    kwargs.setdefault("fg_color", c["surface_elevated"])
    kwargs.setdefault("corner_radius", 18)
    kwargs.setdefault("border_width", 1)
    kwargs.setdefault("border_color", c["border"])
    return ctk.CTkFrame(parent, **kwargs)

def section_header(parent, title, subtitle=None, icon=None):
    """Cabeçalho de seção. `icon` é nome de SVG em assets/icons (sem emoji)."""
    from ui.icons import available, get
    c = get_colors()
    f = ctk.CTkFrame(parent, fg_color="transparent")
    row = ctk.CTkFrame(f, fg_color="transparent")
    row.pack(anchor="w")
    if icon and available(icon):
        ctk.CTkLabel(row, text="", image=get(icon, 24, c["primary"]),
                     width=28).pack(side="left", padx=(0, 8))
    tx = ctk.CTkFrame(row, fg_color="transparent")
    tx.pack(side="left")
    ctk.CTkLabel(tx, text=title, font=FONTS["display"], text_color=c["text"]).pack(anchor="w")
    if subtitle:
        ctk.CTkLabel(tx, text=subtitle, font=FONTS["body"], text_color=c["text_muted"], wraplength=800, justify="left").pack(anchor="w", pady=(2,0))
    return f

def kpi_card(parent, label, value, accent="primary", icon="doc"):
    """KPI estilo Dabang/Horizon: fundo tintado + badge circular com SVG + valor grande."""
    from ui.icons import available, get
    c = get_colors()
    color = c[accent] if accent in c else c["primary"]
    tint = c.get(f"{accent}_tint", c["primary_soft"])
    f = card(parent, fg_color=tint, border_color=color)
    # header: badge + label
    hdr = ctk.CTkFrame(f, fg_color="transparent")
    hdr.pack(fill="x", padx=16, pady=(14, 0))
    badge = ctk.CTkFrame(hdr, width=32, height=32, corner_radius=16, fg_color=color)
    badge.pack(side="left")
    badge.pack_propagate(False)
    if icon and available(icon):
        ctk.CTkLabel(badge, text="",
                     image=get(icon, 16, c["text_on_primary"])).pack(expand=True)
    else:
        ctk.CTkLabel(badge, text="•", font=("Inter", 14, "bold"),
                     text_color=c["text_on_primary"]).pack(expand=True)
    ctk.CTkLabel(hdr, text=label, font=FONTS["caption"], text_color=c["text_muted"]).pack(side="left", padx=10)
    # valor grande
    value_label = ctk.CTkLabel(f, text=value, font=("Inter", 26, "bold"), text_color=c["text"])
    value_label.pack(anchor="w", padx=16, pady=(10, 14))
    f.value_label = value_label
    return f

def pill(parent, text, kind="primary"):
    c = get_colors()
    map_kind = {"primary": c["primary_soft"], "success": c["success_soft"], "warning": c["warning_soft"], "danger": c["danger_soft"], "neutral": c["surface_hover"]}
    txt_color = {"primary": c["primary_hover"], "success": c["success_hover"], "warning": c["warning"], "danger": c["danger"], "neutral": c["text_muted"]}
    lbl = ctk.CTkLabel(parent, text=text, font=FONTS["caption"],
                       fg_color=map_kind.get(kind, c["surface_hover"]), corner_radius=999,
                       padx=12, pady=4, text_color=txt_color.get(kind, c["text"]))
    return lbl

def empty_state(parent, icon, title, subtitle, button_text=None, button_cmd=None):
    from ui.icons import available, get
    c = get_colors()
    f = ctk.CTkFrame(parent, fg_color="transparent")
    if icon and available(icon):
        ctk.CTkLabel(f, text="", image=get(icon, 44, c["icon"])).pack(pady=(20,5))
    ctk.CTkLabel(f, text=title, font=FONTS["h2"], text_color=c["text"]).pack()
    ctk.CTkLabel(f, text=subtitle, font=FONTS["body_small"], text_color=c["text_muted"], wraplength=420, justify="center").pack(pady=(4,12))
    if button_text and button_cmd:
        ctk.CTkButton(f, text=button_text, command=button_cmd, corner_radius=10, fg_color=c["primary"], hover_color=c["primary_hover"], text_color=c["text_on_primary"], height=36).pack()
    return f

def progress_dots(parent, total, done):
    c = get_colors()
    f = ctk.CTkFrame(parent, fg_color="transparent")
    for i in range(total):
        col = c["success"] if i < done else c["border"]
        dot = ctk.CTkFrame(f, width=10, height=10, corner_radius=5, fg_color=col)
        dot.pack(side="left", padx=3)
    return f
