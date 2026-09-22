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
    "primary": "#059669",
    "primary_hover": "#047857",
    "primary_soft": "#ECFDF5",
    "success": "#16A34A",
    "success_soft": "#F0FDF4",
    "success_hover": "#15803D",
    "warning": "#D97706",
    "warning_soft": "#FFFBEB",
    "danger": "#DC2626",
    "danger_soft": "#FEF2F2",
    "accent": "#0D9488",
    "accent_soft": "#F0FDFA",
    "canvas_bg": "#F1F5F9",
    "sidebar": "#0F172A",
    "sidebar_hover": "#1E293B",
    "sidebar_active": "#059669",
    "icon": "#475569",
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
}

FONTS = {
    "display": ("Inter", 22, "bold"),
    "h1": ("Inter", 18, "bold"),
    "h2": ("Inter", 14, "bold"),
    "h3": ("Inter", 12, "bold"),
    "body": ("Inter", 12),
    "body_small": ("Inter", 11),
    "caption": ("Inter", 10),
    "mono": ("JetBrains Mono", 11),
}

def get_colors():
    mode = ctk.get_appearance_mode()
    return DARK if mode == "Dark" else LIGHT

def apply_global():
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("green")
