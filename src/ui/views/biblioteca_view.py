"""
BibliotecaView - lista modelos salvos com busca, preview e ações
"""
import os
from tkinter import messagebox

import customtkinter as ctk

from modelos_salvos import carregar_modelo, listar_modelos, remover_modelo
from ui.components.widgets import card, empty_state, section_header
from ui.icons import get as get_icon
from ui.theme import FONTS, get_colors


class BibliotecaView(ctk.CTkFrame):
    def __init__(self, parent, state, modelo_service, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.state = state
        self.svc = modelo_service
        self.selecionado = None
        self._dirty = True
        self._sig = None
        self._search_after = None
        self._build()
        self.refresh_view()
        self._dirty = False

    def _build(self):
        c = get_colors()
        hdr = section_header(self, "Biblioteca", "Seus modelos salvos ficam aqui — reutilize sem selecionar o arquivo novamente", icon="library")
        hdr.pack(fill="x", padx=24, pady=(18, 8))

        # toolbar: busca + ações
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.pack(fill="x", padx=24, pady=6)
        self.search = ctk.CTkEntry(toolbar, placeholder_text="Buscar por nome…", width=280, height=36, corner_radius=12, border_color=c["border"])
        self.search.pack(side="left")
        self.search.bind("<KeyRelease>", lambda e: self._on_search_key())
        ctk.CTkButton(toolbar, text="Atualizar", image=get_icon("refresh", 16, c["text"]), compound="left",
                      width=110, height=34, corner_radius=12, fg_color=c["surface_elevated"],
                      text_color=c["text"], border_width=1, border_color=c["border"],
                      command=self._refresh).pack(side="left", padx=8)
        ctk.CTkButton(toolbar, text="Usar modelo", width=124, height=36, corner_radius=12, fg_color=c["primary"], hover_color=c["primary_hover"], text_color=c["text_on_primary"], command=self._usar).pack(side="right", padx=6)
        ctk.CTkButton(toolbar, text="Remover", width=96, height=36, corner_radius=12, fg_color=c["danger_soft"], text_color=c["danger"], hover_color=c["danger"], command=self._remover).pack(side="right", padx=6)

        self.list_card = card(self)
        self.list_card.pack(fill="both", expand=True, padx=24, pady=12)
        self.scroll = ctk.CTkScrollableFrame(self.list_card, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=8, pady=8)

        # header
        self.header = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.header.pack(fill="x", pady=(0, 6))
        for txt, w in [("Modelo", 300), ("Tipo", 70), ("Campos", 70), ("Data", 110)]:
            ctk.CTkLabel(self.header, text=txt, font=FONTS["caption"], text_color=c["text_muted"], width=w, anchor="w").pack(side="left", padx=6)

        self.rows_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.rows_frame.pack(fill="both", expand=True)

        self._rows = []

    def _on_search_key(self):
        # debounce: evita rebuild total a cada tecla
        if self._search_after is not None:
            try:
                self.after_cancel(self._search_after)
            except Exception:
                pass
        self._search_after = self.after(200, self._refresh)

    @staticmethod
    def _signature(modelos, query):
        return (tuple((m.get("id"), m.get("nome_original", ""), m.get("tipo", ""),
                       len(m.get("placeholders", [])), m.get("data_adicao", ""))
                      for m in modelos), query)

    def mark_dirty(self):
        self._dirty = True

    def _refresh(self):
        """Rebuild total (botão Atualizar / seleção)."""
        self._sig = None
        self.refresh_view()

    def refresh_view(self):
        """Rebuild barato: só reconstrói se dados/busca mudaram ou tema trocou."""
        try:
            modelos = listar_modelos()
            q = self.search.get().lower().strip()
            sig = self._signature(modelos, q)
            if not self._dirty and sig == self._sig:
                return
            self._sig = sig
            self._render(modelos, q)
            self._dirty = False
        except Exception as e:
            from logger import log_erro
            log_erro(f"Biblioteca refresh_view erro: {e}")

    def _render(self, modelos, q):
        c = get_colors()
        for w in self.rows_frame.winfo_children():
            w.destroy()
        self._rows.clear()
        if q:
            modelos = [m for m in modelos if q in m.get('nome_original', '').lower()]
        if not modelos:
            empty_state(self.rows_frame, "folder", "Nenhum modelo salvo", "Carregue um modelo na aba Modelos e clique em Salvar na Biblioteca.", button_text="Ir para Modelos").pack(pady=20)
            return
        for m in modelos:
            is_sel = self.selecionado == m['id']
            # use surface_elevated for rows, primary border when selected
            r = ctk.CTkFrame(self.rows_frame, fg_color=c["surface_elevated"] if not is_sel else c["surface_hover"], corner_radius=10, border_width=1, border_color=c["primary"] if is_sel else c["border"])
            r.pack(fill="x", pady=3)
            r.bind("<Button-1>", lambda e, mid=m['id'], fr=r: self._select(mid, fr))
            nome = m.get('nome_original', '')[:38]
            tipo = m.get('tipo', '-').upper()
            n = str(len(m.get('placeholders', [])))
            data = m.get('data_adicao', '')[:10]
            for txt, w in [(nome, 300), (tipo, 70), (n, 70), (data, 110)]:
                lbl = ctk.CTkLabel(r, text=txt, font=FONTS["body_small"], width=w, anchor="w", text_color=c["text"])
                lbl.pack(side="left", padx=6, pady=8)
                lbl.bind("<Button-1>", lambda e, mid=m['id'], fr=r: self._select(mid, fr))
            self._rows.append((m['id'], r))

    def _select(self, mid, frame):
        self.selecionado = mid
        self._refresh()

    def _usar(self):
        if not self.selecionado:
            messagebox.showwarning("Aviso", "Selecione um modelo na lista")
            return
        caminho, tipo, phs = carregar_modelo(self.selecionado)
        if not caminho:
            messagebox.showerror("Erro", "Arquivo do modelo não encontrado no disco.")
            self._refresh()
            return
        self.svc.usar_da_biblioteca(caminho, tipo, phs)
        # navega para Mapear? emitir evento
        messagebox.showinfo("Modelo carregado", f"{os.path.basename(caminho)} carregado — {len(phs)} campos")
        # dispara evento para shell trocar aba
        self.event_generate("<<modelo_carregado>>")

    def _remover(self):
        if not self.selecionado:
            messagebox.showwarning("Aviso", "Selecione um modelo")
            return
        if not messagebox.askyesno("Confirmar", "Remover este modelo da biblioteca?"):
            return
        ok, msg = remover_modelo(self.selecionado)
        if ok:
            self.selecionado = None
            self._refresh()
            messagebox.showinfo("Removido", "Modelo removido")
        else:
            messagebox.showerror("Erro", msg)
