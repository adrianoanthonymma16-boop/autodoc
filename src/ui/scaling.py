"""HiDPI scaling for CustomTkinter.

CTk only auto-detects DPI on Windows/macOS; on Linux it always reports 1.0.
Measure physical DPI via Tk and apply widget/window scaling before CTk() is
created so canvas-drawn widgets are not upscaled blurry by the compositor.
"""
from __future__ import annotations

SCALE_MIN = 1.0
SCALE_MAX = 2.5
BASELINE_DPI = 96.0


def clamp_scale(value: float, lo: float = SCALE_MIN, hi: float = SCALE_MAX) -> float:
    if value != value or value <= 0:  # NaN / non-positive
        return lo
    return max(lo, min(hi, float(value)))


def detect_scale_from_dpi(dpi: float, baseline: float = BASELINE_DPI) -> float:
    if baseline <= 0 or dpi <= 0:
        return SCALE_MIN
    # round to 2 decimals so 96.1 DPI does not become a useless 1.001 scale
    return clamp_scale(round(dpi / baseline, 2))


def measure_dpi() -> float:
    import tkinter as tk

    root = None
    try:
        root = tk.Tk()
        root.withdraw()
        return float(root.winfo_fpixels("1i"))
    finally:
        if root is not None:
            root.destroy()


def apply_hidpi_scaling() -> float:
    """Detect display DPI and set CTk scaling. Returns the applied factor."""
    import customtkinter as ctk

    factor = detect_scale_from_dpi(measure_dpi())
    if factor != 1.0:
        ctk.set_widget_scaling(factor)
        ctk.set_window_scaling(factor)
    return factor
