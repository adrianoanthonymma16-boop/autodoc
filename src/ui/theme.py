"""
Design System - AutoDoc Premium
Paleta moderna, responsiva, inspirada em Linear / Stripe
"""
import customtkinter as ctk

LIGHT = {
    "bg": "#F8FAFC",
    "surface": "#FFFFFF",
    "surface_hover": "#F1F5F9",
    "surface_elevated": "#FFFFFF",
    "border": "#E2E8F0",
    "border_strong": "#CBD5E1",
    "text": "#0F172A",
    "text_muted": "#64748B",
    "text_faint": "#94A3B8",
    "text_on_primary": "#FFFFFF",
    "primary": "#047857",
    "primary_hover": "#065F46",
    "primary_soft": "#ECFDF5",
    "success": "#15803D",
    "success_soft": "#F0FDF4",
    "success_hover": "#166534",
    "warning": "#D97706",
    "warning_soft": "#FFFBEB",
    "danger": "#DC2626",
    "danger_soft": "#FEF2F2",
    "accent": "#0F766E",
    "accent_soft": "#F0FDFA",
    "canvas_bg": "#F1F5F9",
    "sidebar": "#0F172A",
    "sidebar_hover": "#1E293B",
    "sidebar_active": "#047857",
    "icon": "#475569",
    # tintados KPI (Dabang) — texto sobre *_soft usa *_hover p/ AA
    "primary_tint": "#ECFDF5",
    "success_tint": "#F0FDF4",
    "accent_tint": "#F0FDFA",
    "warning_tint": "#FFFBEB",
    "danger_tint": "#FEF2F2",
}

DARK = {
    "bg": "#020617",
    "surface": "#0B1220",           # dark blue surface instead of white
    "surface_hover": "#111827",
    "surface_elevated": "#1E293B",   # elevated cards
    "border": "#1E293B",
    "border_strong": "#334155",
    "text": "#E2E8F0",
    "text_muted": "#94A3B8",
    "text_faint": "#64748B",
    "text_on_primary": "#020617",
    "primary": "#10B981",
    "primary_hover": "#059669",
    "primary_soft": "#064E3B",
    "success": "#34D399",
    "success_soft": "#065F46",
    "success_hover": "#10B981",
    "warning": "#F59E0B",
    "warning_soft": "#78350F",
    "danger": "#EF4444",
    "danger_soft": "#7F1D1D",
    "accent": "#2DD4BF",
    "accent_soft": "#134E4A",
    "canvas_bg": "#0B1220",
    "sidebar": "#020617",
    "sidebar_hover": "#0F172A",
    "sidebar_active": "#10B981",
    "icon": "#94A3B8",
    # tintados KPI dark (Vision) — fundos escuros com borda sutil
    "primary_tint": "#064E3B",
    "success_tint": "#065F46",
    "accent_tint": "#134E4A",
    "warning_tint": "#78350F",
    "danger_tint": "#7F1D1D",
}

FONTS = {
    "display": ("Inter", 26, "bold"),
    "h1": ("Inter", 20, "bold"),
    "h2": ("Inter", 15, "bold"),
    "h3": ("Inter", 13, "bold"),
    "body": ("Inter", 12),
    "body_small": ("Inter", 11),
    "caption": ("Inter", 10),
    "mono": ("JetBrains Mono", 11),
}

# Tokens de layout (Dabang / Horizon / Vision)
RADIUS = {"card": 18, "btn": 12, "pill": 999, "input": 12, "nav": 12}
SPACING = {"xs": 4, "sm": 8, "md": 12, "lg": 16, "xl": 24}

def get_colors():
    mode = ctk.get_appearance_mode()
    return DARK if mode == "Dark" else LIGHT

def apply_global():
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("green")
