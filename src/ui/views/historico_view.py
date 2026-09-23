"""
HistoricoView - listagem premium
"""
import os

import customtkinter as ctk

from historico import listar_historico
from ui.components.widgets import card, empty_state, section_header
from ui.icons import get as get_icon
from ui.theme import FONTS, get_colors


class HistoricoView(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._dirty = True
        self._sig = None
        self._build()
        self.refresh_view()
        self._dirty = False

    def _build(self):
        c = get_colors()
        hdr = section_header(self, "Histórico", "Últimos documentos gerados — registro local offline", icon="clock")
        hdr.pack(fill="x", padx=24, pady=(18, 6))
        tb = ctk.CTkFrame(self, fg_color="transparent")
        tb.pack(fill="x", padx=24, pady=6)
        ctk.CTkButton(tb, text="Atualizar", image=get_icon("refresh", 16, c["text"]), compound="left",
                      width=110, height=34, corner_radius=12, fg_color=c["surface_elevated"],
                      text_color=c["text"], border_width=1, border_color=c["border"],
                      command=self.refresh).pack(side="right")
        self.card = card(self)
        self.card.pack(fill="both", expand=True, padx=24, pady=12)
        self.scroll = ctk.CTkScrollableFrame(self.card, fg_color=c["surface_elevated"])
        self.scroll.pack(fill="both", expand=True, padx=8, pady=8)
        self.status = ctk.CTkLabel(self, text="", font=FONTS["caption"], text_color=c["text_muted"])
        self.status.pack(fill="x", padx=20, pady=(0, 10))

    @staticmethod
    def _signature(hist):
        return tuple((h.get("data", ""), h.get("modelo", ""),
                      h.get("saida", ""), h.get("num_campos_preenchidos", ""))
                     for h in hist)

    def refresh(self):
        """Rebuild total (botão Atualizar)."""
        self._sig = None
        self.refresh_view()

    def rebuild_chrome(self):
        """Reconstrói widgets estáticos (pós-toggle de tema)."""
        for w in self.winfo_children():
            w.destroy()
        self._build()

    def refresh_view(self):
        """Rebuild barato: só reconstrói se dados mudaram ou tema trocou."""
        hist = listar_historico()
        sig = self._signature(hist)
        if not self._dirty and sig == self._sig:
            self.status.configure(text=f"{len(hist)} documento(s)" if hist else "Nenhum documento ainda")
            return
        self._sig = sig
        self._render(hist)
        self._dirty = False

    def _render(self, hist):
        c = get_colors()
        for w in self.scroll.winfo_children():
            w.destroy()
        if not hist:
            empty_state(self.scroll, "inbox", "Histórico vazio", "Gere seu primeiro documento na aba Gerar.").pack(pady=40)
            self.status.configure(text="Nenhum documento ainda")
            return
        # header row
        hdr = ctk.CTkFrame(self.scroll, fg_color="transparent")
        hdr.pack(fill="x", pady=(0, 6))
        for t, w in [("Data", 110), ("Modelo", 240), ("Campos", 70), ("Saída", 240)]:
            ctk.CTkLabel(hdr, text=t, font=FONTS["caption"], text_color=c["text_muted"], width=w, anchor="w").pack(side="left", padx=6)
        ctk.CTkFrame(self.scroll, height=1, fg_color=c["border"]).pack(fill="x", pady=4)
        for item in hist:
            r = ctk.CTkFrame(self.scroll, fg_color=c["surface_elevated"], corner_radius=10, border_width=1, border_color=c["border"])
            r.pack(fill="x", pady=3)
            data = item.get('data', '')[:16].replace('T', ' ')
            modelo = os.path.basename(item.get('modelo', '-'))[:28]
            campos = str(item.get('num_campos_preenchidos', '-'))
            saida = os.path.basename(item.get('saida', '-'))[:28]
            for txt, w in [(data, 110), (modelo, 240), (campos, 70), (saida, 240)]:
                ctk.CTkLabel(r, text=txt, font=FONTS["body_small"], width=w, anchor="w", text_color=c["text"]).pack(side="left", padx=6, pady=8)
        self.status.configure(text=f"{len(hist)} documento(s)")
