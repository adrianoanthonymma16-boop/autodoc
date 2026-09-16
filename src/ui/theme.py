"""
Design System - AutoDoc Premium
Paleta moderna, responsiva, inspirada em Linear / Stripe
"""
import customtkinter as ctk

LIGHT = {
    "bg": "#F8FAFC",
    "surface": "#FFFFFF",
    "surface_hover": "#F1F5F9",
    "border": "#E2E8F0",
    "border_strong": "#CBD5E1",
    "text": "#0F172A",
    "text_muted": "#64748B",
    "text_faint": "#94A3B8",
    "primary": "#2563EB",
    "primary_hover": "#1D4ED8",
    "primary_soft": "#EFF6FF",
    "success": "#059669",
    "success_soft": "#ECFDF5",
    "success_hover": "#047857",
    "warning": "#D97706",
    "warning_soft": "#FFFBEB",
    "danger": "#DC2626",
    "danger_soft": "#FEF2F2",
    "accent": "#7C3AED",
    "accent_soft": "#F5F3FF",
    "canvas_bg": "#F1F5F9",
    "sidebar": "#0F172A",
    "sidebar_hover": "#1E293B",
    "sidebar_active": "#2563EB",
}

DARK = {
    "bg": "#020617",
    "surface": "#0F172A",
    "surface_hover": "#1E293B",
    "border": "#1E293B",
    "border_strong": "#334155",
    "text": "#F1F5F9",
    "text_muted": "#94A3B8",
    "text_faint": "#64748B",
    "primary": "#3B82F6",
    "primary_hover": "#2563EB",
    "primary_soft": "#1E293B",
    "success": "#10B981",
    "success_soft": "#064E3B",
    "success_hover": "#059669",
    "warning": "#F59E0B",
    "warning_soft": "#78350F",
    "danger": "#EF4444",
    "danger_soft": "#7F1D1D",
    "accent": "#8B5CF6",
    "accent_soft": "#2E1065",
    "canvas_bg": "#0B1220",
    "sidebar": "#020617",
    "sidebar_hover": "#0F172A",
    "sidebar_active": "#3B82F6",
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
    ctk.set_default_color_theme("blue")
