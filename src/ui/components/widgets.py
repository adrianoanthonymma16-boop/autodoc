"""
Widgets reutilizáveis premium
"""
import customtkinter as ctk

from ui.theme import FONTS, get_colors


def card(parent, **kwargs):
    c = get_colors()
    return ctk.CTkFrame(parent, fg_color=c["surface_elevated"], corner_radius=16,
                        border_width=1, border_color=c["border"], **kwargs)

def section_header(parent, title, subtitle=None, icon=""):
    c = get_colors()
    f = ctk.CTkFrame(parent, fg_color="transparent")
    # Use icon color for the icon
    txt = f"{icon}  {title}" if icon else title
    ctk.CTkLabel(f, text=txt, font=FONTS["h1"], text_color=c["text"]).pack(anchor="w")
    if subtitle:
        ctk.CTkLabel(f, text=subtitle, font=FONTS["body_small"], text_color=c["text_muted"], wraplength=800, justify="left").pack(anchor="w", pady=(2,0))
    return f

def kpi_card(parent, label, value, accent="primary"):
    c = get_colors()
    f = card(parent)
    color = c[accent] if accent in c else c["primary"]
    # top bar
    bar = ctk.CTkFrame(f, height=3, fg_color=color, corner_radius=2)
    bar.pack(fill="x", padx=0, pady=0)
    ctk.CTkLabel(f, text=value, font=("Inter", 24, "bold"), text_color=c["text"]).pack(anchor="w", padx=16, pady=(12,0))
    ctk.CTkLabel(f, text=label, font=FONTS["caption"], text_color=c["text_muted"]).pack(anchor="w", padx=16, pady=(0,12))
    return f

def pill(parent, text, kind="primary"):
    c = get_colors()
    map_kind = {"primary": c["primary_soft"], "success": c["success_soft"], "warning": c["warning_soft"], "danger": c["danger_soft"], "neutral": c["surface_hover"]}
    txt_color = {"primary": c["primary"], "success": c["success"], "warning": c["warning"], "danger": c["danger"], "neutral": c["text_muted"]}
    lbl = ctk.CTkLabel(parent, text=text, font=FONTS["caption"],
                       fg_color=map_kind.get(kind, c["surface_hover"]), corner_radius=20,
                       padx=10, pady=3, text_color=txt_color.get(kind, c["text"]))
    return lbl

def empty_state(parent, icon, title, subtitle, button_text=None, button_cmd=None):
    c = get_colors()
    f = ctk.CTkFrame(parent, fg_color="transparent")
    ctk.CTkLabel(f, text=icon, font=("Inter", 42), text_color=c["icon"]).pack(pady=(20,5))
    ctk.CTkLabel(f, text=title, font=FONTS["h2"], text_color=c["text"]).pack()
    ctk.CTkLabel(f, text=subtitle, font=FONTS["body_small"], text_color=c["text_muted"], wraplength=420, justify="center").pack(pady=(4,12))
    if button_text and button_cmd:
        ctk.CTkButton(f, text=button_text, command=button_cmd, corner_radius=10, fg_color=c["primary"], hover_color=c["primary_hover"], height=36).pack()
    return f

def progress_dots(parent, total, done):
    c = get_colors()
    f = ctk.CTkFrame(parent, fg_color="transparent")
    for i in range(total):
        col = c["success"] if i < done else c["border"]
        dot = ctk.CTkFrame(f, width=10, height=10, corner_radius=5, fg_color=col)
        dot.pack(side="left", padx=3)
    return f
