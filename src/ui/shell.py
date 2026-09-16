"""
Shell - janela principal com sidebar responsiva
"""
import os
import customtkinter as ctk
from ui.theme import get_colors, FONTS
from config import VERSAO
from core.state import AppState
from services.modelo import ModeloService
from services.documento import DocumentoService
from services.mapeamento import MapeamentoService
from services.extracao import ExtracaoService
from services.geracao import GeracaoService
from preferencias import carregar_preferencias, set_preferencia
from logger import log_info
from config import BACKUP_INTERVAL, BACKUP_FILE
import json

from ui.views.modelo_view import ModeloView
from ui.views.biblioteca_view import BibliotecaView
from ui.views.mapeamento_view import MapeamentoView
from ui.views.gerar_view import GerarView
from ui.views.historico_view import HistoricoView


NAV_ITEMS = [
    ("Modelos", "📄", "modelos"),
    ("Biblioteca", "📚", "biblioteca"),
    ("Mapear", "🎯", "mapear"),
    ("Gerar", "✨", "gerar"),
    ("Histórico", "🕘", "historico"),
]

class Shell:
    def __init__(self, root: ctk.CTk):
        self.root = root
        self.state = AppState()
        self.modelo_svc = ModeloService(self.state)
        self.doc_svc = DocumentoService(self.state)
        self.map_svc = MapeamentoService(self.state)
        self.extracao_svc = ExtracaoService(self.state)
        self.geracao_svc = GeracaoService(self.state)

        self._setup_window()
        self._build_layout()
        self._bind_shortcuts()
        self._restore_prefs()
        self._try_restore_backup()
        self._start_backup_loop()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        log_info(f"Shell iniciado v{VERSAO} - modular")

    def _setup_window(self):
        self.root.title(f"AutoDoc  •  v{VERSAO}")
        sw=self.root.winfo_screenwidth(); sh=self.root.winfo_screenheight()
        ww=min(1360, sw-40); wh=min(860, sh-80)
        x=(sw-ww)//2; y=(sh-wh)//2
        self.root.geometry(f"{ww}x{wh}+{x}+{y}")
        self.root.minsize(1020, 640)
        ctk.set_appearance_mode("light")

    def _build_layout(self):
        c = get_colors()
        # root grid: sidebar + main
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        # sidebar
        self.sidebar = ctk.CTkFrame(self.root, fg_color=c["sidebar"], corner_radius=0, width=220)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_rowconfigure(6, weight=1)

        # logo
        logo = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo.pack(fill="x", padx=16, pady=(18,12))
        ctk.CTkLabel(logo, text="◆  AutoDoc", font=("Inter", 18, "bold"), text_color=c["text"]).pack(anchor="w")
        ctk.CTkLabel(logo, text=f"v{VERSAO}  •  Premium", font=("Inter", 10), text_color=c["text_faint"]).pack(anchor="w")

        # nav buttons
        self.nav_btns = {}
        for label, icon, key in NAV_ITEMS:
            btn = ctk.CTkButton(self.sidebar, text=f"{icon}   {label}", anchor="w",
                                fg_color="transparent", hover_color=c["sidebar_hover"],
                                text_color=c["text_muted"], corner_radius=10, height=38,
                                font=("Inter", 12), command=lambda k=key: self._switch(k))
            btn.pack(fill="x", padx=10, pady=3)
            self.nav_btns[key]=btn

        # stepper progress minimal
        self.step_label = ctk.CTkLabel(self.sidebar, text="Progresso", font=("Inter", 10, "bold"), text_color=c["text_faint"])
        self.step_label.pack(anchor="w", padx=16, pady=(16,4))
        self.step_bar = ctk.CTkProgressBar(self.sidebar, height=6, corner_radius=3, progress_color=c["primary"], fg_color=c["sidebar_hover"])
        self.step_bar.pack(fill="x", padx=16); self.step_bar.set(0)

        # bottom actions
        bottom = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        bottom.pack(side="bottom", fill="x", padx=10, pady=12)
        self.btn_theme = ctk.CTkButton(bottom, text="🌙  Modo escuro", height=32, corner_radius=10,
                                       fg_color=c["sidebar_hover"], hover_color=c["border_strong"], text_color=c["text"],
                                       command=self._toggle_theme)
        self.btn_theme.pack(fill="x", pady=4)
        ctk.CTkButton(bottom, text="Sobre", height=28, corner_radius=8, fg_color="transparent",
                      text_color=c["text_faint"], hover_color=c["sidebar_hover"], command=self._sobre).pack(fill="x")

        # main area
        self.main = ctk.CTkFrame(self.root, fg_color=c["bg"], corner_radius=0)
        self.main.grid(row=0, column=1, sticky="nsew")
        self.main.grid_rowconfigure(0, weight=1)
        self.main.grid_columnconfigure(0, weight=1)

        # views container
        self.views = {}
        self.views["modelos"] = ModeloView(self.main, self.state, self.modelo_svc)
        self.views["biblioteca"] = BibliotecaView(self.main, self.state, self.modelo_svc)
        self.views["mapear"] = MapeamentoView(self.main, self.state, self.doc_svc, self.map_svc)
        self.views["gerar"] = GerarView(self.main, self.state, self.extracao_svc, self.geracao_svc)
        self.views["historico"] = HistoricoView(self.main)

        for v in self.views.values():
            v.grid(row=0, column=0, sticky="nsew")

        self.current = None
        self._switch("modelos")
        self.state.subscribe(self._on_state_progress)

    def _on_state_progress(self, ev):
        if ev in ("mapeamento","modelo","modelos"):
            total=len(self.state.placeholders)
            done=len(self.state.mapeamento)
            self.step_bar.set(done/max(1,total))
            if total>0:
                self.step_label.configure(text=f"{done}/{total} mapeados")
            else:
                self.step_label.configure(text="Progresso")

    def _switch(self, key):
        c = get_colors()
        for k, btn in self.nav_btns.items():
            if k==key:
                btn.configure(fg_color=c["primary"], text_color=c["surface"])
            else:
                btn.configure(fg_color="transparent", text_color=c["text_muted"])
        self.views[key].tkraise()
        self.current=key
        # refresh historico when entering
        if key=="historico":
            self.views["historico"].refresh()
        if key=="biblioteca":
            self.views["biblioteca"]._refresh()

    def _bind_shortcuts(self):
        self.root.bind_all('<Control-o>', lambda e: self._switch("modelos"))
        self.root.bind_all('<Control-a>', lambda e: self._switch("mapear"))
        self.root.bind_all('<Control-g>', lambda e: self._switch("gerar"))
        self.root.bind_all('<Control-s>', lambda e: self._save_shortcut())
        self.root.bind_all('<Control-z>', lambda e: self._undo())
        self.root.bind_all('<Control-y>', lambda e: self._redo())
        self.root.bind_all('<Control-d>', lambda e: self._toggle_theme())
        # responsive: collapse sidebar on < 1100 width
        self.root.bind("<Configure>", self._on_resize)

    def _on_resize(self, e):
        if e.widget!=self.root: return
        w=e.width
        if w<1100:
            self.sidebar.configure(width=72)
            # hide text to icons only? keep simple: reduce width
        else:
            self.sidebar.configure(width=220)

    def _save_shortcut(self):
        if self.current=="mapear":
            self.views["mapear"]._salvar()

    def _undo(self):
        ok,msg=self.map_svc.desfazer()
        if self.current=="mapear":
            from tkinter import messagebox
            messagebox.showinfo("Undo" if ok else "Aviso", msg)

    def _redo(self):
        ok,msg=self.map_svc.refazer()
        if self.current=="mapear":
            from tkinter import messagebox
            messagebox.showinfo("Redo" if ok else "Aviso", msg)

    def _toggle_theme(self):
        cur = ctk.get_appearance_mode()
        novo = "Dark" if cur == "Light" else "Light"
        ctk.set_appearance_mode(novo)
        set_preferencia("tema_ctk", novo.lower())
        self.btn_theme.configure(text="☀  Modo claro" if novo == "Dark" else "🌙  Modo escuro")
        log_info(f"Tema: {novo}")
        # Update all theme-dependent components
        self._refresh_theme()

    def _refresh_theme(self):
        """Atualiza todos os componentes com as cores do novo tema"""
        c = get_colors()
        # sidebar
        self.sidebar.configure(fg_color=c["sidebar"])
        # logo
        for child in self.sidebar.winfo_children():
            if isinstance(child, ctk.CTkFrame):  # logo frame
                for label in child.winfo_children():
                    if isinstance(label, ctk.CTkLabel):
                        if "AutoDoc" in label.cget("text"):
                            label.configure(text_color=c["text"])
                        elif "Premium" in label.cget("text"):
                            label.configure(text_color=c["text_faint"])
            elif isinstance(child, ctk.CTkButton):  # nav buttons handled in _switch
                pass
            elif isinstance(child, ctk.CTkLabel):  # step label
                child.configure(text_color=c["text_faint"])
            elif isinstance(child, ctk.CTkProgressBar):
                child.configure(progress_color=c["primary"], fg_color=c["sidebar_hover"])
            elif isinstance(child, ctk.CTkFrame):  # bottom frame
                for btn in child.winfo_children():
                    if isinstance(btn, ctk.CTkButton):
                        if "Modo" in btn.cget("text") or "escuro" in btn.cget("text") or "claro" in btn.cget("text"):
                            btn.configure(fg_color=c["sidebar_hover"], hover_color=c["border_strong"], text_color=c["text"])
                        elif "Sobre" in btn.cget("text"):
                            btn.configure(text_color=c["text_faint"], hover_color=c["sidebar_hover"])
        # main area
        self.main.configure(fg_color=c["bg"])
        # nav buttons
        self._switch(self.current)
        # step bar
        self.step_bar.configure(progress_color=c["primary"], fg_color=c["sidebar_hover"])
        # step label
        self.step_label.configure(text_color=c["text_faint"])
        # trigger view refreshes (they subscribe to state or use get_colors dynamically)
        for view in self.views.values():
            if hasattr(view, '_refresh'):
                view._refresh()

    def _restore_prefs(self):
        prefs=carregar_preferencias()
        tema=prefs.get('tema_ctk','light')
        ctk.set_appearance_mode("Dark" if tema=="dark" else "Light")
        if tema=="dark":
            self.btn_theme.configure(text="☀  Modo claro")
        geo=prefs.get('tamanho_janela_ctk')
        if geo:
            try: self.root.geometry(geo)
            except: pass

    def _try_restore_backup(self):
        data=self.map_svc.restaurar_backup()
        if not data: return
        from tkinter import messagebox
        if messagebox.askyesno("Backup encontrado","Um backup de mapeamento foi encontrado.\nDeseja restaurá-lo?"):
            self.map_svc.aplicar_backup(data)
            log_info("Backup restaurado (shell)")

    def _start_backup_loop(self):
        self.map_svc.backup()
        self.root.after(BACKUP_INTERVAL, self._start_backup_loop)

    def _on_close(self):
        try:
            geo=self.root.geometry()
            set_preferencia('tamanho_janela_ctk', geo)
        except: pass
        log_info("Shell finalizado")
        self.root.destroy()

    def _sobre(self):
        from tkinter import messagebox
        messagebox.showinfo("Sobre", f"AutoDoc v{VERSAO}  •  Premium Modular\n\nArquitetura: core/services/ui desacoplados\nOCR offline • ODT/DOCX • Lote\n\nDesenvolvido por Adriano Anthony\nadrianoanthonymma16@gmail.com\n\n100% offline • MIT")
