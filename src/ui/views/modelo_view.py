"""
ModeloView - aba Modelo com drag&drop, KPIs, lista de modelos carregados
"""
import os
from tkinter import filedialog, messagebox

import customtkinter as ctk

from ui.components.widgets import card, empty_state, kpi_card, pill, section_header
from ui.icons import get as get_icon
from ui.theme import FONTS, get_colors
from validadores import obter_filetypes_modelo


class ModeloView(ctk.CTkFrame):
    def __init__(self, parent, state, modelo_service, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.state = state
        self.svc = modelo_service
        self._dirty = True
        self._search_after = None
        self._build()
        self.state.subscribe(self._on_state)
        self._refresh()
        self._dirty = False

    def mark_dirty(self):
        self._dirty = True

    def refresh_view(self):
        self._refresh()

    def _build(self):
        c = get_colors()
        self.grid_columnconfigure(0, weight=1)

        # header
        hdr = section_header(self, "Modelos", "Carregue seus templates ODT/DOCX com placeholders {{campo}}", icon="doc")
        hdr.pack(fill="x", padx=20, pady=(16,8))

        # KPIs (badge Dabang, ícones SVG)
        kpi_row = ctk.CTkFrame(self, fg_color="transparent")
        kpi_row.pack(fill="x", padx=24, pady=8)
        kpi_row.grid_columnconfigure((0,1,2), weight=1)
        self.kpi_modelos = kpi_card(kpi_row, "Modelos carregados", "0", "primary", icon="doc")
        self.kpi_modelos.grid(row=0, column=0, sticky="ew", padx=6)
        self.kpi_placeholders = kpi_card(kpi_row, "Placeholders únicos", "0", "accent", icon="spark")
        self.kpi_placeholders.grid(row=0, column=1, sticky="ew", padx=6)
        self.kpi_mapeados = kpi_card(kpi_row, "Mapeados", "0/0", "success", icon="check")
        self.kpi_mapeados.grid(row=0, column=2, sticky="ew", padx=6)

        # Drop zone + botões
        drop = card(self)
        drop.pack(fill="x", padx=24, pady=10)
        ctk.CTkLabel(drop, text="Arraste e solte aqui ou clique para selecionar", font=FONTS["body"], text_color=c["text_muted"]).pack(pady=(18,4))
        ctk.CTkLabel(drop, text="ODT e DOCX • placeholders no formato {{nome_campo}}", font=FONTS["caption"], text_color=c["text_faint"]).pack()
        btn_row = ctk.CTkFrame(drop, fg_color="transparent")
        btn_row.pack(pady=14)
        ctk.CTkButton(btn_row, text="Carregar Modelo", command=self._carregar, corner_radius=12, fg_color=c["primary"], hover_color=c["primary_hover"], text_color=c["text_on_primary"], height=40, font=FONTS["h3"]).pack(side="left", padx=6)
        ctk.CTkButton(btn_row, text="Adicionar ao lote", image=get_icon("plus", 16, c["primary_hover"]), compound="left", command=self._adicionar_lote, corner_radius=12, fg_color=c["surface_hover"], text_color=c["primary_hover"], border_width=1, border_color=c["primary"], hover_color=c["primary_soft"], height=40).pack(side="left", padx=6)
        # drag drop bindings (tkdnd se disponível tenta)
        drop.bind("<Button-1>", lambda e: self._carregar())

        # Placeholders grid
        self.ph_card = card(self)
        self.ph_card.pack(fill="both", expand=True, padx=20, pady=10)
        ctk.CTkLabel(self.ph_card, text="Placeholders", font=FONTS["h2"], text_color=c["text"]).pack(anchor="w", padx=16, pady=(12,4))
        # search
        self.search = ctk.CTkEntry(self.ph_card, placeholder_text="Buscar placeholder…", height=34, corner_radius=10, border_color=c["border"])
        self.search.pack(fill="x", padx=16, pady=(0,8))
        self.search.bind("<KeyRelease>", lambda e: self._on_search_key())

        self.ph_scroll = ctk.CTkScrollableFrame(self.ph_card, height=180, fg_color="transparent")
        self.ph_scroll.pack(fill="both", expand=True, padx=8, pady=(0,8))

        # Modelos carregados tabela leve
        self.lote_card = card(self)
        # pack só quando há modelos
        self.lote_scroll = ctk.CTkScrollableFrame(self.lote_card, height=110, fg_color="transparent")

        # Ações de salvar
        self.save_row = ctk.CTkFrame(self, fg_color="transparent")
        self.save_row.pack(fill="x", padx=20, pady=(0,10))
        ctk.CTkButton(self.save_row, text="Salvar na Biblioteca", image=get_icon("save", 16, c["text_on_primary"]), compound="left", command=self._salvar_biblioteca, corner_radius=10, fg_color=c["success"], hover_color=c["success_hover"], text_color=c["text_on_primary"], height=36).pack(side="left")
        self.lbl_status = ctk.CTkLabel(self.save_row, text="Nenhum modelo carregado", font=FONTS["caption"], text_color=c["text_muted"])
        self.lbl_status.pack(side="left", padx=12)

    def _on_search_key(self):
        # debounce: evita rebuild total a cada tecla
        if self._search_after is not None:
            try:
                self.after_cancel(self._search_after)
            except Exception:
                pass
        self._search_after = self.after(200, self._render_placeholders)

    def _on_state(self, ev):
        if ev in ("modelo","modelos","mapeamento","backup"):
            self._refresh()
            self._dirty = False

    def _refresh(self):
        get_colors()
        n_modelos = len(self.state.modelos) if self.state.modelos else (1 if self.state.modelo_path else 0)
        n_ph = len(self.state.placeholders)
        n_map = len(self.state.mapeamento)
        self.kpi_modelos.value_label.configure(text=str(n_modelos))
        self.kpi_placeholders.value_label.configure(text=str(n_ph))
        self.kpi_mapeados.value_label.configure(text=f"{n_map}/{n_ph}" if n_ph else "0/0")
        self._render_placeholders()
        self._render_lote()

        if self.state.placeholders:
            self.lbl_status.configure(text=f"{n_ph} placeholders • {n_map} mapeados")
        else:
            self.lbl_status.configure(text="Nenhum modelo carregado")

    def _render_placeholders(self):
        c = get_colors()
        for w in self.ph_scroll.winfo_children():
            w.destroy()
        filtro = self.search.get().strip().lower()
        if not self.state.placeholders:
            empty_state(self.ph_scroll, "search", "Nenhum placeholder", "Carregue um modelo ODT/DOCX com {{campo}}.", button_text="Carregar Modelo", button_cmd=self._carregar).pack(pady=20)
            return
        # grid de chips
        row = None
        for ph in self.state.placeholders:
            if filtro and filtro not in ph.lower():
                continue
            mapped = ph in self.state.mapeamento
            prefix = "✓" if mapped else "○"
            row = ctk.CTkFrame(self.ph_scroll, fg_color=c["surface_hover"] if not mapped else c["success_soft"], corner_radius=10, border_width=1, border_color=c["success"] if mapped else c["border"])
            row.pack(fill="x", pady=3, padx=4)
            ctk.CTkLabel(row, text=f"{prefix}  {{{{{ph}}}}}", font=FONTS["body_small"], text_color=c["success_hover"] if mapped else c["text"]).pack(side="left", padx=10, pady=6)
            pill(row, "mapeado" if mapped else "pendente", "success" if mapped else "neutral").pack(side="right", padx=8)

    def _render_lote(self):
        c = get_colors()
        if not self.state.modelos:
            if self.lote_card.winfo_ismapped():
                self.lote_card.pack_forget()
            return
        if not self.lote_card.winfo_ismapped():
            self.lote_card.pack(fill="x", padx=20, pady=(0,10))
            ctk.CTkLabel(self.lote_card, text="Lote de modelos", font=FONTS["h3"], text_color=c["text"]).pack(anchor="w", padx=16, pady=(10,4))
            self.lote_scroll.pack(fill="x", padx=8, pady=(0,8))
        for w in self.lote_scroll.winfo_children():
            w.destroy()
        for i, m in enumerate(self.state.modelos):
            r = ctk.CTkFrame(self.lote_scroll, fg_color="transparent")
            r.pack(fill="x", pady=2)
            ctk.CTkLabel(r, text=os.path.basename(m['path']), font=FONTS["body_small"], width=220, anchor="w").pack(side="left", padx=6)
            pill(r, m['tipo'].upper(), "primary").pack(side="left", padx=4)
            ctk.CTkLabel(r, text=", ".join(m['placeholders'])[:60], font=FONTS["caption"], text_color=c["text_muted"], width=260, anchor="w").pack(side="left", padx=6)
            ctk.CTkButton(r, text="", image=get_icon("x", 14, c["danger"]), width=28, height=24, corner_radius=8, fg_color=c["danger_soft"], hover_color=c["danger"], command=lambda idx=i: self.svc.remover_do_lote(idx)).pack(side="right", padx=4)

    def _carregar(self):
        from mensagens import mostrar_info_modelos
        if not mostrar_info_modelos():
            return
        from preferencias import carregar_preferencias, set_preferencia
        prefs = carregar_preferencias()
        dir_ini = prefs.get('ultimo_diretorio_modelo', os.path.expanduser("~"))
        caminho = filedialog.askopenfilename(title="Selecione o modelo (ODT/DOCX)", filetypes=obter_filetypes_modelo(), initialdir=dir_ini)
        if not caminho:
            return
        set_preferencia('ultimo_diretorio_modelo', os.path.dirname(caminho))
        ok, msg = self.svc.carregar_arquivo_unico(caminho)
        if not ok:
            messagebox.showwarning("Aviso", msg)
        else:
            # toast via status
            self.lbl_status.configure(text=f"Carregado: {os.path.basename(caminho)} — {msg}")

    def _adicionar_lote(self):
        from preferencias import carregar_preferencias
        prefs = carregar_preferencias()
        dir_ini = prefs.get('ultimo_diretorio_modelo', os.path.expanduser("~"))
        caminhos = filedialog.askopenfilenames(title="Selecione modelos (ODT/DOCX)", filetypes=obter_filetypes_modelo(), initialdir=dir_ini)
        for cam in caminhos:
            ok, msg = self.svc.adicionar_ao_lote(cam)
            if not ok:
                messagebox.showwarning("Aviso", f"{os.path.basename(cam)}: {msg}")

    def _salvar_biblioteca(self):
        if not self.state.modelo_path:
            messagebox.showwarning("Aviso", "Carregue um modelo primeiro!")
            return
        from mensagens import mostrar_modelo_ja_salvo, mostrar_modelo_salvo_sucesso
        from modelos_salvos import salvar_modelo
        ok, _msg = salvar_modelo(self.state.modelo_path, self.state.modelo_tipo, self.state.placeholders)
        if ok:
            mostrar_modelo_salvo_sucesso(os.path.basename(self.state.modelo_path))
        else:
            mostrar_modelo_ja_salvo(os.path.basename(self.state.modelo_path))
