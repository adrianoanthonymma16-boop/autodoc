"""
Janela de seleção visual: documento inteiro, recorte e confirmação do valor.

Fluxo:
1. Abre em janela própria com a página inteira ajustada à tela.
2. Usuário arrasta sobre a região do placeholder.
3. OCR roda em thread e o valor volta num campo editável.
4. Usuário confirma (salva o mapeamento) ou edita manualmente antes.
5. Com vários campos pendentes, "Salvar e próximo" avança na mesma janela,
   mantendo os retângulos já confirmados como referência.
"""

import contextlib
import queue
import threading

import customtkinter as ctk
from PIL import Image

from config import CONF_BOA, CONF_MEDIA
from ocr import extrair_texto_com_confianca
from ui import messagebox
from ui.canvas.image_canvas import ImageCanvas
from ui.components.widgets import card
from ui.icons import get as get_icon
from ui.theme import FONTS, get_colors


class RegionWindow(ctk.CTkToplevel):
    def __init__(
        self,
        parent,
        imagem,
        placeholders,
        documento_nome,
        retangulos=None,
        on_confirm=None,
    ):
        super().__init__(parent)
        self.imagem = imagem
        self.placeholders = list(placeholders)
        self.documento_nome = documento_nome
        self.on_confirm = on_confirm
        self._refs = [dict(r) for r in (retangulos or [])]
        self.indice = 0
        self._salvos = 0
        self._rect = None
        self._confianca = None
        self._seq = 0
        self._ocr_fila = queue.Queue()

        c = get_colors()
        self.title(f"Selecionar área de {self.placeholders[0]}")
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        largura = min(1400, int(sw * 0.92))
        altura = min(900, int(sh * 0.90))
        self.geometry(f"{largura}x{altura}+{(sw - largura) // 2}+{(sh - altura) // 2}")
        self.minsize(900, 560)
        self.bind("<Escape>", lambda e: self.destroy())

        cab = ctk.CTkFrame(self, fg_color="transparent")
        cab.pack(fill="x", padx=18, pady=(14, 6))
        linha = ctk.CTkFrame(cab, fg_color="transparent")
        linha.pack(fill="x")
        ctk.CTkLabel(
            linha, text="", image=get_icon("target", 26, c["primary"]), width=30, height=30
        ).pack(side="left", anchor="n", padx=(0, 10), pady=(2, 0))
        textos = ctk.CTkFrame(linha, fg_color="transparent")
        textos.pack(side="left", anchor="n", fill="x", expand=True)
        self.lbl_titulo = ctk.CTkLabel(
            textos, text="", font=FONTS["display"], text_color=c["text"]
        )
        self.lbl_titulo.pack(anchor="w")
        self.lbl_sub = ctk.CTkLabel(
            textos, text="", font=FONTS["body"], text_color=c["text_muted"],
            wraplength=820, justify="left",
        )
        self.lbl_sub.pack(anchor="w", pady=(2, 0))
        cab.bind(
            "<Configure>",
            lambda e: self.lbl_sub.configure(wraplength=max(320, e.width - 80)),
        )

        self.card_canvas = card(self)
        self.card_canvas.pack(fill="both", expand=True, padx=14, pady=4)
        self.canvas = ImageCanvas(
            self.card_canvas, on_rect_done=self._on_rect, fg_color="transparent"
        )
        self.canvas.pack(fill="both", expand=True, padx=6, pady=6)

        self.lbl_status = ctk.CTkLabel(
            self, text="", font=FONTS["caption"], text_color=c["text_muted"]
        )
        self.lbl_status.pack(fill="x", padx=18, pady=(2, 4))

        self.painel = ctk.CTkFrame(self, fg_color="transparent")
        self.painel.pack(fill="x", padx=18, pady=(0, 12))

        self.canvas.set_image(imagem)
        self._aplicar_overlays()
        self._atualizar_cabecalho()
        self.after(250, self.canvas.fit_to_view)
        self.after(150, self._tornar_modal)
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self._poll_ocr()

    def _tornar_modal(self):
        with contextlib.suppress(Exception):
            self.transient(self.master.winfo_toplevel())
            self.grab_set()

    # --- sequência ---
    def _placeholder(self):
        return self.placeholders[self.indice]

    def _atualizar_cabecalho(self):
        ph = self._placeholder()
        total = len(self.placeholders)
        self.lbl_titulo.configure(text=f"Selecione a área de {{{ph}}}")
        self.lbl_sub.configure(
            text=(
                f"{self.documento_nome} — campo {self.indice + 1} de {total}. "
                "Arraste sobre o valor; depois confirme ou edite o texto lido."
            )
        )
        self.lbl_status.configure(text="Arraste sobre o valor para selecionar a área.")
        self.title(f"Selecionar área de {ph}")

    def _aplicar_overlays(self):
        c = get_colors()

        def overlay(cv):
            cv.draw_rects(self._refs, color=c["success"], label_color=c["success"])

        self.canvas.set_overlays([overlay])

    def _iniciar_campo(self):
        self._rect = None
        self._confianca = None
        self.canvas.permitir_selecao = True
        self.canvas.limpar_selecao()
        self._limpar_painel()
        self._atualizar_cabecalho()
        self._aplicar_overlays()

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
        self._ocr_fila.put((seq, texto, conf, recorte))

    def _poll_ocr(self):
        try:
            seq, texto, conf, recorte = self._ocr_fila.get_nowait()
        except queue.Empty:
            with contextlib.suppress(Exception):
                if self.winfo_exists():
                    self.after(100, self._poll_ocr)
            return
        self._mostrar_confirmacao(texto, conf, recorte, seq)
        with contextlib.suppress(Exception):
            if self.winfo_exists():
                self.after(100, self._poll_ocr)

    def _limpar_painel(self):
        self.entrada = None
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
        self.lbl_status.configure(
            text="Confira o valor lido. Se estiver errado, edite antes de confirmar."
        )

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
        ultimo = self.indice >= len(self.placeholders) - 1
        ctk.CTkButton(
            botoes,
            text="Salvar e concluir" if ultimo else "Salvar e próximo campo",
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
            text="Fechar",
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
        ph = self._placeholder()
        valor = self.entrada.get().strip()
        if not valor and not messagebox.askyesno(
            "Campo vazio",
            f"O campo '{ph}' ficará vazio. Confirmar mesmo assim?",
        ):
            return
        if self.on_confirm:
            self.on_confirm(ph, self._rect, valor, self._confianca)
        self._refs = [r for r in self._refs if r.get("label") != ph]
        self._refs.append({**self._rect, "label": ph})
        self._salvos += 1
        self.indice += 1
        if self.indice < len(self.placeholders):
            self._iniciar_campo()
        else:
            self._mostrar_resumo()

    def _selecionar_de_novo(self):
        self._rect = None
        self._limpar_painel()
        self.canvas.limpar_selecao()
        self.lbl_status.configure(text="Arraste novamente sobre o valor.")

    def _mostrar_resumo(self):
        c = get_colors()
        self._seq += 1
        self.canvas.permitir_selecao = False
        self.canvas.limpar_selecao()
        self._limpar_painel()
        self.lbl_titulo.configure(text="Seleção concluída")
        n = self._salvos
        self.lbl_sub.configure(
            text=f"{n} campo{'s' if n != 1 else ''} mapeado{'s' if n != 1 else ''} em {self.documento_nome}."
        )
        self.lbl_status.configure(text="Você pode fechar a janela ou remapear clicando na lista.")
        box = card(self.painel)
        box.pack(fill="x")
        ctk.CTkLabel(
            box,
            text=f"{n} campo{'s' if n != 1 else ''} confirmado{'s' if n != 1 else ''} neste documento.",
            font=FONTS["body"], text_color=c["success"],
        ).pack(side="left", padx=12, pady=12)
        ctk.CTkButton(
            box,
            text="Fechar",
            image=get_icon("check", 16, c["text_on_primary"]),
            compound="left",
            height=36,
            corner_radius=10,
            fg_color=c["success"],
            hover_color=c["success_hover"],
            text_color=c["text_on_primary"],
            command=self.destroy,
        ).pack(side="right", padx=12, pady=8)
