#!/usr/bin/env python3
"""
AutoDoc - Ponto de Entrada
Usa a nova interface modular (ui.shell.Shell / CustomTkinter) como primário,
com fallback para a interface legada ttkbootstrap apenas quando a nova
interface (ou suas dependências) não estão disponíveis.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))


def _show_error(msg):
    try:
        import tkinter as tk
        from tkinter import messagebox
        r = tk.Tk(); r.withdraw()
        messagebox.showerror("AutoDoc - Erro", msg)
        r.destroy()
    except Exception:
        print(msg, file=sys.stderr)
    try:
        import subprocess
        subprocess.run(["zenity", "--error", f"--text={msg}", "--title=AutoDoc Erro"], check=False)
    except Exception:
        pass


def _start_nova():
    """Tenta a interface moderna. True se iniciou; False se indisponível."""
    try:
        import customtkinter as ctk
        from ui.scaling import apply_hidpi_scaling
        from ui.shell import Shell
        apply_hidpi_scaling()
        root = ctk.CTk()
        app = Shell(root)
        root.mainloop()
        return True
    except ImportError as e:
        try:
            from logger import log_erro
            log_erro(f"Interface moderna indisponível ({e}), usando legada")
        except Exception:
            pass
        return False
    except Exception as e:
        import traceback
        traceback.print_exc()
        try:
            from logger import log_erro
            log_erro(f"Falha nova interface: {e}")
        except Exception:
            pass
        # runtime failure da moderna → tenta a legada
        return False


def _start_legacy():
    """Interface legada ttkbootstrap (AppDocumentos)."""
    import ttkbootstrap as ttk
    from interface import AppDocumentos
    root = ttk.Window(themename="cosmo")
    app = AppDocumentos(root)
    root.mainloop()


if __name__ == "__main__":
    if _start_nova():
        sys.exit(0)
    try:
        _start_legacy()
        sys.exit(0)
    except Exception as e:
        import traceback
        traceback.print_exc()
        _show_error(f"Falha ao iniciar AutoDoc:\n{e}")
        sys.exit(1)