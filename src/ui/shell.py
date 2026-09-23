"""
Shell - janela principal com sidebar responsiva
"""
import contextlib

import customtkinter as ctk

from config import BACKUP_INTERVAL, VERSAO
from core.state import AppState
from logger import log_info
from preferencias import carregar_preferencias, set_preferencia
from services.documento import DocumentoService
from services.extracao import ExtracaoService
from services.geracao import GeracaoService
from services.mapeamento import MapeamentoService
from services.modelo import ModeloService
from ui.icons import get as get_icon
from ui.theme import get_colors

NAV_ITEMS = [
    ("Modelos", "doc", "modelos"),
    ("Biblioteca", "library", "biblioteca"),
    ("Mapear", "target", "mapear"),
    ("Gerar", "spark", "gerar"),
    ("Histórico", "clock", "historico"),
]


class Shell:
    def __init__(self, root: ctk.CTk):
        self.root = root
        self._collapsed = None
        self._resize_after = None
        self.state = AppState()
        self.modelo_svc = ModeloService(self.state)
        self.doc_svc = DocumentoService(self.state)
        self.map_svc = MapeamentoService(self.state)
        self.extracao_svc = ExtracaoService(self.state)
        self.geracao_svc = GeracaoService(self.state)

        self.views = {}
        self._view_factories = {
            "modelos": self._make_modelos,
            "biblioteca": self._make_biblioteca,
            "mapear": self._make_mapear,
            "gerar": self._make_gerar,
            "historico": self._make_historico,
        }
        self._setup_window()
        self._build_layout()
        self._bind_shortcuts()
        self._restore_prefs()
        self._try_restore_backup()
        self._start_backup_loop()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        log_info(f"Shell iniciado v{VERSAO} - modular")

    # --- lazy factories: só a view visível é construída (startup rápido) ---
    def _make_modelos(self):
        from ui.views.modelo_view import ModeloView
        return ModeloView(self.main, self.state, self.modelo_svc)

    def _make_biblioteca(self):
        from ui.views.biblioteca_view import BibliotecaView
        return BibliotecaView(self.main, self.state, self.modelo_svc)

    def _make_mapear(self):
        from ui.views.mapeamento_view import MapeamentoView
        return MapeamentoView(self.main, self.state, self.doc_svc, self.map_svc)

    def _make_gerar(self):
        from ui.views.gerar_view import GerarView
        return GerarView(self.main, self.state, self.extracao_svc, self.geracao_svc)

    def _make_historico(self):
        from ui.views.historico_view import HistoricoView
        return HistoricoView(self.main)

    def _ensure_view(self, key):
        view = self.views.get(key)
        if view is None:
            view = self._view_factories[key]()
            view.grid(row=0, column=0, sticky="nsew")
            self.views[key] = view
        return view

    def _setup_window(self):
        self.root.title(f"AutoDoc  •  v{VERSAO}")
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        ww = min(1360, sw - 40)
        wh = min(860, sh - 80)
        x = (sw - ww) // 2
        y = (sh - wh) // 2
        self.root.geometry(f"{ww}x{wh}+{x}+{y}")
        self.root.minsize(1020, 640)
        from preferencias import carregar_preferencias
        tema = carregar_preferencias().get('tema_ctk', 'light')
        ctk.set_appearance_mode("Dark" if tema == "dark" else "Light")

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

        # logo — badge squircle + wordmark (Dabang)
        logo = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo.pack(fill="x", padx=16, pady=(20, 16))
        row = ctk.CTkFrame(logo, fg_color="transparent")
        row.pack(anchor="w")
        mark = ctk.CTkFrame(row, width=36, height=36, corner_radius=10, fg_color=c["primary"])
        mark.pack(side="left", ipady=0)
        mark.pack_propagate(False)
        ctk.CTkLabel(mark, text="", image=get_icon("spark", 18, c["text_on_primary"])).pack(expand=True)
        texts = ctk.CTkFrame(row, fg_color="transparent")
        texts.pack(side="left", padx=10)
        ctk.CTkLabel(texts, text="AutoDoc", font=("Inter", 17, "bold"), text_color=c["text"]).pack(anchor="w")
        ctk.CTkLabel(texts, text=f"v{VERSAO} • Premium", font=("Inter", 10), text_color=c["text_faint"]).pack(anchor="w")
        self._logo_texts = texts

        # nav buttons — pill ativa estilo Dabang/Horizon, ícones SVG
        self.nav_btns = {}
        self.nav_icons = {}
        for label, icon, key in NAV_ITEMS:
            btn = ctk.CTkButton(self.sidebar, text=label, image=get_icon(icon, 18, c["text_muted"]),
                                compound="left", anchor="w",
                                fg_color="transparent", hover_color=c["sidebar_hover"],
                                text_color=c["text_muted"], corner_radius=12, height=40,
                                font=("Inter", 13), command=lambda k=key: self._switch(k))
            btn.pack(fill="x", padx=12, pady=3)
            self.nav_btns[key] = btn
            self.nav_icons[key] = icon

        # stepper progress minimal
        self.step_label = ctk.CTkLabel(self.sidebar, text="Progresso", font=("Inter", 10, "bold"), text_color=c["text_faint"])
        self.step_label.pack(anchor="w", padx=16, pady=(16, 4))
        self.step_bar = ctk.CTkProgressBar(self.sidebar, height=8, corner_radius=4, progress_color=c["primary"], fg_color=c["sidebar_hover"])
        self.step_bar.pack(fill="x", padx=16)
        self.step_bar.set(0)

        # bottom actions
        bottom = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        bottom.pack(side="bottom", fill="x", padx=10, pady=12)
        self.btn_theme = ctk.CTkButton(bottom, text="Modo escuro", image=get_icon("moon", 16, c["text"]),
                                       compound="left", height=32, corner_radius=10,
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

        self.current = None
        self._switch("modelos")
        self.state.subscribe(self._on_state_progress)

    def _nav_style(self, key, active):
        c = get_colors()
        btn = self.nav_btns[key]
        color = c["text_on_primary"] if active else c["text_muted"]
        collapsed = bool(self._collapsed)
        label = "" if collapsed else dict((k, lbl) for lbl, _, k in NAV_ITEMS)[key]
        btn.configure(
            image=get_icon(self.nav_icons[key], 18, color),
            text=label,
            fg_color=c["primary"] if active else "transparent",
            text_color=color,
            hover_color=c["primary_hover"] if active else c["sidebar_hover"],
        )

    def _on_state_progress(self, ev):
        if ev in ("mapeamento", "modelo", "modelos"):
            total = len(self.state.placeholders)
            done = len(self.state.mapeamento)
            self.step_bar.set(done / max(1, total))
            if total > 0:
                self.step_label.configure(text=f"{done}/{total} mapeados")
            else:
                self.step_label.configure(text="Progresso")

    def _switch(self, key):
        view = self._ensure_view(key)
        for k in self.nav_btns:
            self._nav_style(k, k == key)
        view.tkraise()
        self.current = key
        # rebuild quando dirty (tema) ou dados mudaram: cromo estático
        # primeiro (rebuild_chrome), depois listas (refresh_view decide
        # pelo _dirty + assinatura). Flag limpa DEPOIS.
        if getattr(view, "_dirty", False):
            if hasattr(view, "rebuild_chrome"):
                view.rebuild_chrome()
            if hasattr(view, "refresh_view"):
                view.refresh_view()
            view._dirty = False

    def _bind_shortcuts(self):
        self.root.bind_all('<Control-o>', lambda e: self._switch("modelos"))
        self.root.bind_all('<Control-a>', lambda e: self._switch("mapear"))
        self.root.bind_all('<Control-g>', lambda e: self._switch("gerar"))
        self.root.bind_all('<Control-s>', lambda e: self._save_shortcut())
        self.root.bind_all('<Control-z>', lambda e: self._undo())
        self.root.bind_all('<Control-y>', lambda e: self._redo())
        self.root.bind_all('<Control-d>', lambda e: self._toggle_theme())
        # responsive: collapse sidebar on < 1100 width (debounced)
        self.root.bind("<Configure>", self._on_resize)

    def _on_resize(self, e):
        # <Configure> borbulha dos filhos: ignora tudo que não é a janela
        # (compara pelo path Tk, robusto a wrappers Python distintos)
        if getattr(e.widget, "_w", e.widget) != self.root._w:
            return
        if self._resize_after is not None:
            with contextlib.suppress(Exception):
                self.root.after_cancel(self._resize_after)
        self._resize_after = self.root.after(120, self._apply_resize)

    def _apply_resize(self):
        self._resize_after = None
        try:
            w = self.root.winfo_width()
        except Exception:
            return
        collapsed = w < 1100
        # idempotente — evita Configure storm (sidebar width/pack dispara novo Configure)
        if self._collapsed == collapsed:
            return
        self._collapsed = collapsed
        if collapsed:
            self.sidebar.configure(width=72)
        else:
            self.sidebar.configure(width=232)
        # icon-only na sidebar colapsada (responsividade)
        for key in self.nav_btns:
            self._nav_style(key, key == self.current)
        if hasattr(self, "_logo_texts"):
            for child in self._logo_texts.winfo_children():
                if collapsed:
                    child.pack_forget()
                else:
                    child.pack(anchor="w")
        if collapsed:
            self.step_label.pack_forget()
            self.step_bar.pack_forget()
        else:
            self.step_label.pack(anchor="w", padx=16, pady=(16, 4))
            self.step_bar.pack(fill="x", padx=16)

    def _save_shortcut(self):
        if self.current == "mapear":
            self.views["mapear"]._salvar()

    def _undo(self):
        ok, msg = self.map_svc.desfazer()
        if self.current == "mapear":
            from tkinter import messagebox
            messagebox.showinfo("Undo" if ok else "Aviso", msg)

    def _redo(self):
        ok, msg = self.map_svc.refazer()
        if self.current == "mapear":
            from tkinter import messagebox
            messagebox.showinfo("Redo" if ok else "Aviso", msg)

    def _toggle_theme(self):
        cur = ctk.get_appearance_mode()
        novo = "Dark" if cur == "Light" else "Light"
        ctk.set_appearance_mode(novo)
        set_preferencia("tema_ctk", novo.lower())
        log_info(f"Tema: {novo}")
        self._refresh_theme()

    def _refresh_theme(self):
        """Recolore shell; views não-visíveis são marcadas dirty (rebuild lazy)."""
        c = get_colors()
        dark = ctk.get_appearance_mode() == "Dark"
        self.sidebar.configure(fg_color=c["sidebar"])
        self.main.configure(fg_color=c["bg"])
        self.step_bar.configure(progress_color=c["primary"], fg_color=c["sidebar_hover"])
        self.step_label.configure(text_color=c["text_faint"])
        self.btn_theme.configure(
            image=get_icon("sun" if dark else "moon", 16, c["text"]),
            text="Modo claro" if dark else "Modo escuro",
            fg_color=c["sidebar_hover"], hover_color=c["border_strong"], text_color=c["text"],
        )
        for key, btn in self.nav_btns.items():
            self._nav_style(key, key == self.current)
        for key, view in self.views.items():
            view._dirty = True
        if self.current and self.current in self.views:
            view = self.views[self.current]
            # rebuild total da visível: cromo estático (_build) + listas
            if hasattr(view, "rebuild_chrome"):
                view.rebuild_chrome()
            if hasattr(view, "refresh_view"):
                view.refresh_view()
            view._dirty = False

    def _restore_prefs(self):
        prefs = carregar_preferencias()
        tema = prefs.get('tema_ctk', 'light')
        ctk.set_appearance_mode("Dark" if tema == "dark" else "Light")
        dark = tema == "dark"
        c = get_colors()
        self.btn_theme.configure(
            image=get_icon("sun" if dark else "moon", 16, c["text"]),
            text="Modo claro" if dark else "Modo escuro",
        )
        geo = prefs.get('tamanho_janela_ctk')
        if geo:
            with contextlib.suppress(BaseException):
                self.root.geometry(geo)

    def _try_restore_backup(self):
        data = self.map_svc.restaurar_backup()
        if not data:
            return
        from tkinter import messagebox
        if messagebox.askyesno("Backup encontrado", "Um backup de mapeamento foi encontrado.\nDeseja restaurá-lo?"):
            self.map_svc.aplicar_backup(data)
            log_info("Backup restaurado (shell)")

    def _start_backup_loop(self):
        self.map_svc.backup()
        self.root.after(BACKUP_INTERVAL, self._start_backup_loop)

    def _on_close(self):
        try:
            geo = self.root.geometry()
            set_preferencia('tamanho_janela_ctk', geo)
        except Exception:
            pass
        log_info("Shell finalizado")
        self.root.destroy()

    def _sobre(self):
        from tkinter import messagebox
        messagebox.showinfo("Sobre", f"AutoDoc v{VERSAO}  •  Premium Modular\n\nArquitetura: core/services/ui desacoplados\nOCR offline • ODT/DOCX • Lote\n\nDesenvolvido por Adriano Anthony\nadrianoanthonymma16@gmail.com\n\n100% offline • MIT")
