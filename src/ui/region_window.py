"""
Janela de seleção visual: todas as páginas dos documentos anexados.

Fluxo:
1. Abre em janela própria com as páginas empilhadas (scroll vertical).
2. Usuário arrasta sobre a região do placeholder, em qualquer página.
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
from logger import log_erro
from ocr import extrair_texto_com_confianca
from ui import messagebox
from ui.canvas.image_canvas import ImageCanvas
from ui.components.widgets import card
from ui.icons import get as get_icon
from ui.selection_pages import (
    CABECALHO,
    montar_composto,
    pagina_do_retangulo,
    recorte_local,
    retangulo_composto,
)
from ui.theme import FONTS, get_colors


class RegionWindow(ctk.CTkToplevel):
    def __init__(self, parent, documentos, placeholders, retangulos=None, on_confirm=None):
        super().__init__(parent)
        self.placeholders = list(placeholders)
        self.documentos = documentos
        self.on_confirm = on_confirm
        self._refs = [dict(r) for r in (retangulos or [])]
        self._alvo = None
        self.indice = 0
        self._salvos = 0
        self._seq = 0
        self._ocr_fila = queue.Queue()

        self.composto, self.paginas = montar_composto(documentos)
        nomes = {r.get('label') for r in self._refs if r.get('label')}
        self._confirmados = len(nomes)

        c = get_colors()
        self.title(f"Selecionar área de {self.placeholders[0]}")
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        largura = min(1500, int(sw * 0.92))
        altura = min(950, int(sh * 0.92))
        self.geometry(f"{largura}x{altura}+{(sw - largura) // 2}+{(sh - altura) // 2}")
        self.minsize(900, 600)
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

        barra = ctk.CTkFrame(self, fg_color="transparent")
        barra.pack(fill="x", padx=18, pady=(0, 6))
        ctk.CTkLabel(
            barra, text="Campo", font=FONTS["caption"], text_color=c["text_muted"]
        ).pack(side="left")
        self._rotulos_campo = [
            f"{i + 1} de {len(self.placeholders)} · {ph}"
            for i, ph in enumerate(self.placeholders)
        ]
        self.opt_campo = ctk.CTkOptionMenu(
            barra,
            values=self._rotulos_campo,
            width=280,
            height=30,
            font=FONTS["caption"],
            fg_color=c["surface_elevated"],
            button_color=c["primary"],
            button_hover_color=c["primary_hover"],
            text_color=c["text"],
            dropdown_fg_color=c["surface_elevated"],
            dropdown_text_color=c["text"],
            command=self._ir_para_campo,
        )
        self.opt_campo.pack(side="left", padx=(6, 0))

        ctk.CTkButton(
            barra,
            text="",
            image=get_icon("chevron-right", 16, c["text"]),
            width=30,
            height=30,
            fg_color="transparent",
            hover_color=c["surface_hover"],
            command=lambda: self._passo_pagina(1),
        ).pack(side="right")
        self.lbl_pagina = ctk.CTkLabel(
            barra, text="", font=FONTS["caption"], text_color=c["text_muted"]
        )
        self.lbl_pagina.pack(side="right", padx=8)
        ctk.CTkButton(
            barra,
            text="",
            image=get_icon("chevron-left", 16, c["text"]),
            width=30,
            height=30,
            fg_color="transparent",
            hover_color=c["surface_hover"],
            command=lambda: self._passo_pagina(-1),
        ).pack(side="right")

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

        self.canvas.set_image(self.composto)
        self._aplicar_overlays()
        self._atualizar_cabecalho()
        self.opt_campo.set(self._rotulos_campo[0])
        self.bind("<Prior>", lambda e: self._passo_pagina(-1))
        self.bind("<Next>", lambda e: self._passo_pagina(1))
        self.after(250, self.canvas.fit_to_width)
        self.after(320, self._atualizar_pagina)
        alvo = self._pagina_do_campo(self._placeholder())
        if alvo is not None:
            self.after(340, lambda i=alvo: self._ir_para_pagina(i))
        self.after(150, self._tornar_modal)
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self._poll_ocr()
        self.after(400, self._sync_pagina)

    def _tornar_modal(self):
        with contextlib.suppress(Exception):
            self.transient(self.master.winfo_toplevel())
            self.grab_set()

    # --- sequência ---
    def _placeholder(self):
        return self.placeholders[self.indice]

    def _atualizar_cabecalho(self, confirmados=None):
        ph = self._placeholder()
        total = len(self.placeholders)
        confirmados = self._confirmados if confirmados is None else confirmados
        self.lbl_titulo.configure(text=f"Selecione a área de {{{ph}}}")
        self.lbl_sub.configure(
            text=(
                f"Campo {self.indice + 1} de {total} · {confirmados} já confirmado"
                f"{'s' if confirmados != 1 else ''}. Arraste sobre o valor em qualquer "
                "página; use o seletor de campo ou as setas para navegar."
            )
        )
        self.lbl_status.configure(text="Arraste sobre o valor em qualquer página.")
        self.title(f"Selecionar área de {ph}")
        self.opt_campo.set(self._rotulos_campo[self.indice])

    # --- navegação entre campos e páginas ---
    def _ir_para_campo(self, rotulo):
        with contextlib.suppress(ValueError):
            indice = self._rotulos_campo.index(rotulo)
            if indice != self.indice:
                self._selecionar_campo(indice)

    def _selecionar_campo(self, indice):
        if not 0 <= indice < len(self.placeholders):
            return
        self.indice = indice
        self._iniciar_campo()

    def _pagina_do_campo(self, campo):
        chave = None
        for ref in self._refs:
            if ref.get('label') == campo:
                chave = (ref.get('documento_path'), ref.get('pagina', 0))
                break
        if chave is None:
            return None
        for indice, pagina in enumerate(self.paginas):
            if (pagina['documento_path'], pagina['pagina']) == chave:
                return indice
        return None

    def _indice_pagina_visivel(self):
        if not self.canvas.imagem_resized or not self.canvas.imagem_original:
            return 0
        escala = self.canvas.imagem_resized.height / max(
            1, self.canvas.imagem_original.height
        )
        topo = self.canvas.canvas.canvasy(0)
        y = (topo - self.canvas.pan_y) / max(escala, 1e-6)
        indice = 0
        for i, pagina in enumerate(self.paginas):
            if pagina['y'] <= y + 30:
                indice = i
        return indice

    def _atualizar_pagina(self):
        if not self.paginas:
            return
        indice = self._indice_pagina_visivel()
        pagina = self.paginas[indice]
        nome = pagina['documento_nome'] or 'documento'
        if len(nome) > 26:
            nome = nome[:23] + '...'
        self.lbl_pagina.configure(
            text=f"{nome} · {pagina['pagina'] + 1}/{pagina['total_paginas']}"
        )

    def _sync_pagina(self):
        try:
            if not self.winfo_exists():
                return
            self._atualizar_pagina()
            self.after(400, self._sync_pagina)
        except Exception:
            return

    def _ir_para_pagina(self, indice):
        if not 0 <= indice < len(self.paginas):
            return
        if not self.canvas.imagem_resized or not self.canvas.imagem_original:
            return
        pagina = self.paginas[indice]
        escala = self.canvas.imagem_resized.height / max(
            1, self.canvas.imagem_original.height
        )
        y = pagina['y'] * escala + self.canvas.pan_y
        altura = max(1, self.canvas.imagem_resized.height)
        self.canvas.canvas.yview_moveto(max(0.0, min(1.0, (y - 6) / altura)))
        self._atualizar_pagina()

    def _passo_pagina(self, delta):
        atual = self._indice_pagina_visivel()
        self._ir_para_pagina(max(0, min(len(self.paginas) - 1, atual + delta)))

    def _refs_compostas(self):
        por_chave = {(p['documento_path'], p['pagina']): p for p in self.paginas}
        resultado = []
        for r in self._refs:
            chave = (r.get('documento_path'), r.get('pagina', 0))
            pagina = por_chave.get(chave)
            if pagina is None:
                continue
            base = retangulo_composto(pagina, r['x1'], r['y1'], r['x2'], r['y2'])
            base['campo'] = r.get('label')
            base['label'] = f"✓ {r['label']}" if r.get('label') else ""
            resultado.append(base)
        return resultado

    def _aplicar_overlays(self):
        c = get_colors()
        atual = (
            self.placeholders[self.indice]
            if self.indice < len(self.placeholders)
            else None
        )

        def overlay(cv):
            refs = self._refs_compostas()
            cv.draw_rects(
                [r for r in refs if r.get('campo') != atual],
                color=c["success"], label_color=c["success"],
            )
            cv.draw_rects(
                [r for r in refs if r.get('campo') == atual],
                color=c["primary"], label_color=c["primary"],
            )
            if not cv.imagem_original or not cv.imagem_resized:
                return
            sx = cv.imagem_resized.width / cv.imagem_original.width
            sy = cv.imagem_resized.height / cv.imagem_original.height
            for pagina in self.paginas:
                x = pagina['x'] * sx + cv.pan_x
                y = (pagina['y'] - CABECALHO) * sy + cv.pan_y
                nome = pagina['documento_nome'] or 'documento'
                texto = f"{nome} — página {pagina['pagina'] + 1} de {pagina['total_paginas']}"
                cv.canvas.create_text(
                    x, y, text=texto, anchor="sw", fill=c["text_muted"],
                    font=("Inter", 9, "bold"),
                )

        self.canvas.set_overlays([overlay])

    def _iniciar_campo(self):
        self._seq += 1
        self._alvo = None
        self.canvas.permitir_selecao = True
        self.canvas.limpar_selecao()
        self._limpar_painel()
        self._atualizar_cabecalho()
        self._aplicar_overlays()
        alvo = self._pagina_do_campo(self._placeholder())
        if alvo is not None:
            self.after(30, lambda i=alvo: self._ir_para_pagina(i))

    # --- seleção ---
    def _on_rect(self, x1, y1, x2, y2):
        if x2 - x1 < 4 or y2 - y1 < 4:
            return
        pagina = pagina_do_retangulo(self.paginas, x1, y1, x2, y2)
        local = recorte_local(pagina, x1, y1, x2, y2) if pagina else None
        if pagina is None or local is None:
            self.lbl_status.configure(text="Selecione a área dentro de uma página.")
            self.canvas.limpar_selecao()
            return
        self._seq += 1
        seq = self._seq
        self._alvo = {'pagina': pagina, 'local': local}
        self._limpar_painel()
        self.lbl_status.configure(text="Lendo a região com OCR…")
        recorte = pagina['imagem'].crop(local)
        threading.Thread(
            target=self._ler_recorte, args=(recorte, seq), daemon=True
        ).start()

    def _ler_recorte(self, recorte, seq):
        texto, conf, erro = "", 0.0, None
        try:
            texto, conf = extrair_texto_com_confianca(recorte)
        except Exception as exc:
            erro = str(exc) or type(exc).__name__
            log_erro(f"OCR da seleção falhou: {erro}")
        self._ocr_fila.put((seq, texto, conf, recorte, erro))

    def _poll_ocr(self):
        try:
            seq, texto, conf, recorte, erro = self._ocr_fila.get_nowait()
        except queue.Empty:
            with contextlib.suppress(Exception):
                if self.winfo_exists():
                    self.after(100, self._poll_ocr)
            return
        self._mostrar_confirmacao(texto, conf, recorte, seq, erro)
        with contextlib.suppress(Exception):
            if self.winfo_exists():
                self.after(100, self._poll_ocr)

    def _limpar_painel(self):
        self.entrada = None
        for w in self.painel.winfo_children():
            w.destroy()

    def _mostrar_confirmacao(self, texto, conf, recorte, seq, erro=None):
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
        elif erro:
            txt_conf, cor = f"OCR falhou: {erro}. Digite o valor manualmente.", c["danger"]
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

    def _mapeados(self):
        return {r.get('label') for r in self._refs if r.get('label')}

    # --- ações ---
    def _confirmar(self):
        if not self._alvo:
            return
        ph = self._placeholder()
        valor = self.entrada.get().strip()
        if not valor and not messagebox.askyesno(
            "Campo vazio",
            f"O campo '{ph}' ficará vazio. Confirmar mesmo assim?",
        ):
            return
        pagina = self._alvo['pagina']
        local = self._alvo['local']
        if self.on_confirm:
            doc = {
                'caminho': pagina['documento_path'],
                'nome': pagina['documento_nome'],
                'tipo': pagina['documento_tipo'],
            }
            self.on_confirm(ph, doc, pagina['pagina'], local, valor, self._confianca)
        self._refs = [r for r in self._refs if r.get('label') != ph]
        self._refs.append({
            'documento_path': pagina['documento_path'],
            'pagina': pagina['pagina'],
            'x1': local[0], 'y1': local[1], 'x2': local[2], 'y2': local[3],
            'label': ph,
        })
        self._salvos += 1
        self._confirmados = len(self._mapeados())
        self.indice += 1
        if self.indice < len(self.placeholders):
            self._iniciar_campo()
        else:
            self._mostrar_resumo()

    def _selecionar_de_novo(self):
        self._seq += 1
        self._alvo = None
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
            text=f"{n} campo{'s' if n != 1 else ''} mapeado{'s' if n != 1 else ''} nesta seleção."
        )
        self.lbl_status.configure(
            text="Feche a janela ou clique em Remapear para ajustar um campo."
        )
        box = card(self.painel)
        box.pack(fill="x")
        ctk.CTkLabel(
            box,
            text=f"{n} campo{'s' if n != 1 else ''} confirmado{'s' if n != 1 else ''}.",
            font=FONTS["body"], text_color=c["success"],
        ).pack(side="left", padx=12, pady=12)
        ctk.CTkButton(
            box,
            text="Remapear",
            height=36,
            corner_radius=10,
            fg_color="transparent",
            border_width=1,
            border_color=c["border"],
            text_color=c["text"],
            command=lambda: self._selecionar_campo(0),
        ).pack(side="right", padx=(0, 6))
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
        ).pack(side="right", padx=12)
