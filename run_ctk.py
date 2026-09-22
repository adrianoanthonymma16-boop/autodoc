#!/usr/bin/env python3
"""
AutoDoc - Entry Point Premium Modular
Usa nova Shell (ui/shell.py) com fallback para interface_ctk legacy
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

def _show_error(msg):
    try:
        import tkinter as tk
        from tkinter import messagebox
        r=tk.Tk(); r.withdraw()
        messagebox.showerror("AutoDoc - Erro", msg)
        r.destroy()
    except Exception:
        print(msg, file=sys.stderr)
    try:
        import subprocess
        subprocess.run(["zenity","--error", f"--text={msg}", "--title=AutoDoc Erro"], check=False)
    except Exception:
        pass

try:
    import customtkinter as ctk
except ImportError as e:
    _show_error("CustomTkinter não encontrado.\n\nInstale com:\n  pip install customtkinter\n\nErro: "+str(e))
    sys.exit(1)

try:
    from ui.shell import Shell
    NEW_SHELL = True
    _fallback_error = None
except Exception as e:
    NEW_SHELL = False
    _fallback_error = str(e)
    # log but don't popup yet
    try:
        from logger import log_erro
        log_erro(f"Nova shell não carregou: {e}")
    except: pass

if __name__ == "__main__":
    if NEW_SHELL:
        try:
            from ui.scaling import apply_hidpi_scaling
            apply_hidpi_scaling()
            root = ctk.CTk()
            app = Shell(root)
            root.mainloop()
        except Exception as e:
            import traceback
            traceback.print_exc()
            try:
                from logger import log_erro
                log_erro(f"Falha nova interface: {e}")
            except: pass
            # fallback silencioso para legada, sem popup assustador
            try:
                from interface_ctk import AppDocumentosCTK
                root = ctk.CTk()
                app = AppDocumentosCTK(root)
                root.mainloop()
            except Exception as e2:
                traceback.print_exc()
                _show_error(f"Falha ao iniciar AutoDoc:\n{e2}\n\nOriginal: {e}")
                sys.exit(1)
    else:
        # nova shell não importou, log e vai direto para legada sem popup prévio
        try:
            from logger import log_erro
            log_erro(f"Nova shell import falhou ({_fallback_error}), usando legada")
        except: pass
        from interface_ctk import AppDocumentosCTK
        from ui.scaling import apply_hidpi_scaling
        apply_hidpi_scaling()
        root = ctk.CTk()
        app = AppDocumentosCTK(root)
        root.mainloop()
