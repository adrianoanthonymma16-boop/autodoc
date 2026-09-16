"""
HistoricoView - listagem premium
"""
import os
import customtkinter as ctk
from ui.theme import get_colors, FONTS
from ui.components.widgets import card, section_header, empty_state
from historico import listar_historico

class HistoricoView(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._build()
        self.refresh()

    def _build(self):
        hdr=section_header(self, "Histórico", "Últimos documentos gerados — registro local offline", icon="🕘")
        hdr.pack(fill="x", padx=20, pady=(16,6))
        tb=ctk.CTkFrame(self, fg_color="transparent")
        tb.pack(fill="x", padx=20, pady=6)
        ctk.CTkButton(tb, text="↻ Atualizar", width=100, height=32, corner_radius=10, fg_color=get_colors()["surface"], text_color=get_colors()["text"], border_width=1, border_color=get_colors()["border"], command=self.refresh).pack(side="right")
        self.card=card(self)
        self.card.pack(fill="both", expand=True, padx=20, pady=10)
        self.scroll=ctk.CTkScrollableFrame(self.card, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=8, pady=8)
        self.status=ctk.CTkLabel(self, text="", font=FONTS["caption"], text_color=get_colors()["text_muted"])
        self.status.pack(fill="x", padx=20, pady=(0,10))

    def refresh(self):
        c=get_colors()
        for w in self.scroll.winfo_children(): w.destroy()
        hist=listar_historico()
        if not hist:
            empty_state(self.scroll, "📭", "Histórico vazio", "Gere seu primeiro documento na aba Gerar.").pack(pady=40)
            self.status.configure(text="Nenhum documento ainda")
            return
        # header row
        hdr=ctk.CTkFrame(self.scroll, fg_color="transparent")
        hdr.pack(fill="x", pady=(0,6))
        for t,w in [("Data",110),("Modelo",240),("Campos",70),("Saída",240)]:
            ctk.CTkLabel(hdr, text=t, font=FONTS["caption"], text_color=c["text_muted"], width=w, anchor="w").pack(side="left", padx=6)
        ctk.CTkFrame(self.scroll, height=1, fg_color=c["border"]).pack(fill="x", pady=4)
        for item in hist:
            r=ctk.CTkFrame(self.scroll, fg_color=c["surface_hover"], corner_radius=10)
            r.pack(fill="x", pady=3)
            data=item.get('data','')[:16].replace('T',' ')
            modelo=os.path.basename(item.get('modelo','-'))[:28]
            campos=str(item.get('num_campos_preenchidos','-'))
            saida=os.path.basename(item.get('saida','-'))[:28]
            for txt,w in [(data,110),(modelo,240),(campos,70),(saida,240)]:
                ctk.CTkLabel(r, text=txt, font=FONTS["body_small"], width=w, anchor="w").pack(side="left", padx=6, pady=8)
        self.status.configure(text=f"{len(hist)} documento(s)")
