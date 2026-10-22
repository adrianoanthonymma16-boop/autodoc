"""
Janela de seleção visual: documento inteiro, recorte e confirmação do valor.

Fluxo:
1. Abre em janela própria com a página inteira ajustada à tela.
2. Usuário arrasta sobre a região do placeholder.
3. OCR roda em thread e o valor volta num campo editável.
4. Usuário confirma (salva o mapeamento) ou edita manualmente antes.
"""

import contextlib
import threading

import customtkinter as ctk
from PIL import Image

from config import CONF_BOA, CONF_MEDIA
from ocr import extrair_texto_com_confianca
from ui import messagebox
from ui.canvas.image_canvas import ImageCanvas
from ui.components.widgets import card, section_header
from ui.icons import get as get_icon
from ui.theme import FONTS, get_colors


class RegionWindow(ctk.CTkToplevel):
    def __init__(self, parent, imagem, placeholder, documento_nome, on_confirm):
        super().__init__(parent)
        self.imagem = imagem
        self.placeholder = placeholder
        self.on_confirm = on_confirm
        self._rect = None
        self._confianca = None
        self._seq = 0

        c = get_colors()
        self.title(f"Selecionar área de {placeholder}")
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        largura = min(1400, int(sw * 0.92))
        altura = min(900, int(sh * 0.90))
        self.geometry(f"{largura}x{altura}+{(sw - largura) // 2}+{(sh - altura) // 2}")
        self.minsize(900, 560)

        cab = section_header(
            self,
            f"Selecione a área de {{{{{placeholder}}}}}",
            f"{documento_nome} — arraste sobre o valor. Depois confirme ou edite o texto lido.",
            icon="target",
        )
        cab.pack(fill="x", padx=18, pady=(14, 6))

        self.card_canvas = card(self)
        self.card_canvas.pack(fill="both", expand=True, padx=14, pady=4)
        self.canvas = ImageCanvas(
            self.card_canvas, on_rect_done=self._on_rect, fg_color="transparent"
        )
        self.canvas.pack(fill="both", expand=True, padx=6, pady=6)

        self.lbl_status = ctk.CTkLabel(
            self,
            text="Arraste sobre o valor para selecionar a área.",
            font=FONTS["caption"],
            text_color=c["text_muted"],
        )
        self.lbl_status.pack(fill="x", padx=18, pady=(2, 4))

        self.painel = ctk.CTkFrame(self, fg_color="transparent")
        self.painel.pack(fill="x", padx=18, pady=(0, 12))

        self.canvas.set_image(imagem)
        self.after(250, self.canvas.fit_to_view)
        self.after(150, self._tornar_modal)
        self.protocol("WM_DELETE_WINDOW", self.destroy)

    def _tornar_modal(self):
        try:
            self.transient(self.master.winfo_toplevel())
            self.grab_set()
        except Exception:
            pass

    # --- seleção ---
    def _on_rect(self, x1, y1, x2, y2):
        if x2 - x1 < 4 or y2 - y1 < 4:
            return
        self._seq += 1
        seq = self._seq
        self._rect = {"x1": x1, "y1": y1, "x2": x2, "y2": y2}
        self._confianca = None
        self._limpar_painel()
        self.lbl_status.configure(text="Lendo a região com OCR…")
        recorte = self.imagem.crop((x1, y1, x2, y2))
        threading.Thread(
            target=self._ler_recorte, args=(recorte, seq), daemon=True
        ).start()

    def _ler_recorte(self, recorte, seq):
        texto, conf = "", 0.0
        try:
            texto, conf = extrair_texto_com_confianca(recorte)
        except Exception:
            texto, conf = "", 0.0
        with contextlib.suppress(Exception):
            self.after(
                0,
                lambda: self._mostrar_confirmacao(texto, conf, recorte, seq),
            )

    def _limpar_painel(self):
        for w in self.painel.winfo_children():
            w.destroy()

    def _mostrar_confirmacao(self, texto, conf, recorte, seq):
        if seq != self._seq:
            return
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return
        self._confianca = conf if texto else 0.0
        c = get_colors()
        self.lbl_status.configure(text="Confira o valor lido. Se estiver errado, edite antes de confirmar.")

        box = card(self.painel)
        box.pack(fill="x")

        topo = ctk.CTkFrame(box, fg_color="transparent")
        topo.pack(fill="x", padx=12, pady=(10, 4))

        mini = recorte.copy()
        mini.thumbnail((220, 64), Image.Resampling.LANCZOS)
        self._thumb = ctk.CTkImage(
            light_image=mini, dark_image=mini, size=(mini.width, mini.height)
        )
        ctk.CTkLabel(topo, text="", image=self._thumb).pack(side="left", padx=(0, 10))

        if texto:
            if conf >= CONF_BOA:
                txt_conf, cor = f"Extraído com confiança alta ({conf:.0f}%)", c["success"]
            elif conf >= CONF_MEDIA:
                txt_conf, cor = f"Extraído com confiança média ({conf:.0f}%)", c["warning"]
            else:
                txt_conf, cor = f"Extraído com confiança baixa ({conf:.0f}%)", c["danger"]
        else:
            txt_conf, cor = "Nada foi lido nesta área. Digite o valor manualmente.", c["warning"]
        ctk.CTkLabel(
            topo, text=txt_conf, font=FONTS["body_small"], text_color=cor
        ).pack(side="left")

        linha = ctk.CTkFrame(box, fg_color="transparent")
        linha.pack(fill="x", padx=12, pady=4)
        self.entrada = ctk.CTkEntry(
            linha,
            height=36,
            corner_radius=10,
            border_color=c["border"],
            placeholder_text="Valor do campo",
        )
        self.entrada.pack(side="left", fill="x", expand=True)
        if texto:
            self.entrada.insert(0, texto)
        self.entrada.bind("<Return>", lambda e: self._confirmar())

        botoes = ctk.CTkFrame(box, fg_color="transparent")
        botoes.pack(fill="x", padx=12, pady=(2, 10))
        ctk.CTkButton(
            botoes,
            text="Confirmar valor",
            image=get_icon("check", 16, c["text_on_primary"]),
            compound="left",
            height=36,
            corner_radius=10,
            fg_color=c["success"],
            hover_color=c["success_hover"],
            text_color=c["text_on_primary"],
            command=self._confirmar,
        ).pack(side="left")
        ctk.CTkButton(
            botoes,
            text="Selecionar de novo",
            height=36,
            corner_radius=10,
            fg_color="transparent",
            border_width=1,
            border_color=c["border"],
            text_color=c["text"],
            command=self._selecionar_de_novo,
        ).pack(side="left", padx=6)
        ctk.CTkButton(
            botoes,
            text="Cancelar",
            image=get_icon("x", 14, c["danger"]),
            compound="left",
            height=36,
            corner_radius=10,
            fg_color=c["danger_soft"],
            hover_color=c["danger_soft_hover"],
            text_color=c["danger"],
            command=self.destroy,
        ).pack(side="left")

        self.entrada.focus_set()
        self.entrada.icursor("end")

    # --- ações ---
    def _confirmar(self):
        if not self._rect:
            return
        valor = self.entrada.get().strip()
        if not valor and not messagebox.askyesno(
            "Campo vazio",
            f"O campo '{self.placeholder}' ficará vazio. Confirmar mesmo assim?",
        ):
            return
        self.on_confirm(self._rect, valor, self._confianca)
        self.destroy()

    def _selecionar_de_novo(self):
        self._rect = None
        self._limpar_painel()
        self.canvas.limpar_selecao()
        self.lbl_status.configure(text="Arraste novamente sobre o valor.")
