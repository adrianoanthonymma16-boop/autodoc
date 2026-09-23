"""
MapeamentoView - placeholder list + documento list + canvas moderno
"""
import os
from tkinter import filedialog, messagebox

import customtkinter as ctk

from ui.canvas.image_canvas import ImageCanvas
from ui.components.widgets import card, section_header
from ui.icons import get as get_icon
from ui.theme import FONTS, get_colors
from validadores import obter_filetypes_anexo


class MapeamentoView(ctk.CTkFrame):
    def __init__(self, parent, state, doc_service, map_service, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.state = state
        self.doc_svc = doc_service
        self.map_svc = map_service
        self.canvas = None
        self._dirty = True
        self._search_after = None
        self._build()
        self.state.subscribe(self._on_state)
        self._dirty = False

    def mark_dirty(self):
        self._dirty = True

    def refresh_view(self):
        self._render_all()

    def rebuild_chrome(self):
        """Reconstrói widgets estáticos (pós-toggle), preservando imagem, retângulo e busca."""
        img = self.canvas.imagem_original if self.canvas else None
        pending = self._pending_rect
        q = self.search_ph.get() if hasattr(self, "search_ph") else ""
        for w in self.winfo_children():
            w.destroy()
        self.canvas = None
        self._build()
        self._pending_rect = pending
        if q:
            self.search_ph.insert(0, q)
        if img is not None:
            self.canvas.set_image(img)

    def _build(self):
        c = get_colors()
        hdr = section_header(self, "Mapear", "Selecione o placeholder e o documento, depois desenhe o retângulo no visualizador", icon="target")
        hdr.pack(fill="x", padx=24, pady=(14,6))

        # Step indicator + progress
        self.step = ctk.CTkFrame(self, fg_color="transparent")
        self.step.pack(fill="x", padx=24, pady=4)
        self.lbl_progress = ctk.CTkLabel(self.step, text="0/0 mapeados", font=FONTS["caption"], text_color=c["text_muted"])
        self.lbl_progress.pack(side="left")
        self.prog = ctk.CTkProgressBar(self.step, height=8, corner_radius=4, progress_color=c["success"], fg_color=c["border"])
        self.prog.pack(side="left", fill="x", expand=True, padx=12)
        self.prog.set(0)

        # Toolbar
        tb = ctk.CTkFrame(self, fg_color="transparent")
        tb.pack(fill="x", padx=24, pady=6)
        ctk.CTkButton(tb, text="Anexar", image=get_icon("plus", 16, c["text_on_primary"]), compound="left", height=34, corner_radius=12, fg_color=c["success"], hover_color=c["success_hover"], text_color=c["text_on_primary"], command=self._anexar).pack(side="left", padx=4)
        ctk.CTkButton(tb, text="Limpar mapeamento", height=34, corner_radius=12, fg_color=c["warning_soft"], text_color=c["warning"], hover_color=c["warning"], command=self._limpar).pack(side="left", padx=4)
        ctk.CTkButton(tb, text="Remover doc", height=34, corner_radius=12, fg_color=c["danger_soft"], text_color=c["danger"], hover_color=c["danger"], command=self._remover_doc).pack(side="left", padx=4)
        ctk.CTkButton(tb, text="Desfazer", image=get_icon("undo", 16, c["text"]), compound="left", height=32, corner_radius=12, fg_color="transparent", border_width=1, border_color=c["border"], text_color=c["text"], command=self._undo).pack(side="right", padx=3)
        ctk.CTkButton(tb, text="Exportar", height=32, corner_radius=12, fg_color="transparent", border_width=1, border_color=c["primary"], text_color=c["primary_hover"], command=self._export).pack(side="right", padx=3)
        ctk.CTkButton(tb, text="Importar", height=32, corner_radius=12, fg_color="transparent", border_width=1, border_color=c["primary"], text_color=c["primary_hover"], command=self._import).pack(side="right", padx=3)

        # Instrução
        instr = ctk.CTkFrame(self, fg_color=c["primary_soft"], corner_radius=12, border_width=1, border_color=c["primary"])
        instr.pack(fill="x", padx=24, pady=6)
        ctk.CTkLabel(instr, text="1. Escolha o campo   →   2. Escolha o documento   →   3. Desenhe no visualizador   →   4. Clique em SALVAR MAPEAMENTO", font=("Inter", 10, "bold"), text_color=c["primary_hover"]).pack(pady=8)

        # Dual lists
        dual = ctk.CTkFrame(self, fg_color="transparent")
        dual.pack(fill="x", padx=24, pady=6)
        dual.grid_columnconfigure((0,1), weight=1)

        left = card(dual)
        left.grid(row=0, column=0, sticky="nsew", padx=4)
        ctk.CTkLabel(left, text="Campos", font=FONTS["h3"]).pack(anchor="w", padx=12, pady=(10,4))
        self.search_ph = ctk.CTkEntry(left, placeholder_text="Buscar campo…", height=28, corner_radius=8, border_color=c["border"])
        self.search_ph.pack(fill="x", padx=10, pady=(0,6))
        self.search_ph.bind("<KeyRelease>", lambda e: self._on_search_key())

        self.ph_scroll = ctk.CTkScrollableFrame(left, height=140, fg_color=c["surface_elevated"])
        self.ph_scroll.pack(fill="both", expand=True, padx=6, pady=(0,6))

        right = card(dual)
        right.grid(row=0, column=1, sticky="nsew", padx=4)
        ctk.CTkLabel(right, text="Documentos", font=FONTS["h3"]).pack(anchor="w", padx=12, pady=(10,4))
        self.doc_scroll = ctk.CTkScrollableFrame(right, height=140, fg_color=c["surface_elevated"])
        self.doc_scroll.pack(fill="both", expand=True, padx=6, pady=(0,6))

        # Status selection
        status = ctk.CTkFrame(self, fg_color="transparent")
        status.pack(fill="x", padx=20, pady=2)
        self.lbl_ph_sel = ctk.CTkLabel(status, text="Campo: —", font=FONTS["body_small"], text_color=c["primary_hover"])
        self.lbl_ph_sel.pack(side="left")
        self.lbl_doc_sel = ctk.CTkLabel(status, text="Documento: —", font=FONTS["body_small"], text_color=c["success_hover"])
        self.lbl_doc_sel.pack(side="right")

        # Canvas
        self.canvas_card = card(self)
        self.canvas_card.pack(fill="both", expand=True, padx=20, pady=6)
        self.canvas = ImageCanvas(self.canvas_card, on_rect_done=self._on_rect, fg_color="transparent")
        self.canvas.pack(fill="both", expand=True, padx=8, pady=8)

        # Mapeamentos + salvar
        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.pack(fill="x", padx=24, pady=(0,6))
        ctk.CTkButton(bottom, text="SALVAR MAPEAMENTO", image=get_icon("save", 18, c["text_on_primary"]), compound="left", height=44, corner_radius=12, fg_color=c["primary"], hover_color=c["primary_hover"], text_color=c["text_on_primary"], font=("Inter", 13, "bold"), command=self._salvar).pack(fill="x")

        self.map_card = card(self)
        self.map_card.pack(fill="x", padx=24, pady=(0,12))
        ctk.CTkLabel(self.map_card, text="Mapeamentos", font=FONTS["caption"], text_color=c["text_muted"]).pack(anchor="w", padx=12, pady=(6,2))
        self.map_scroll = ctk.CTkScrollableFrame(self.map_card, height=80, fg_color=c["surface_elevated"])
        self.map_scroll.pack(fill="both", expand=True, padx=6, pady=(0,6))
        self.lbl_status = ctk.CTkLabel(self, text="Aguardando modelo…", font=FONTS["caption"], text_color=c["text_muted"])
        self.lbl_status.pack(fill="x", padx=20)

        self._pending_rect = None
        self._render_all()

    def _on_search_key(self):
        # debounce: evita rebuild total a cada tecla
        if self._search_after is not None:
            try:
                self.after_cancel(self._search_after)
            except Exception:
                pass
        self._search_after = self.after(200, self._render_ph)

    def _on_state(self, ev):
        if ev in ("modelo","modelos","mapeamento","documentos","doc_selecionado","backup"):
            self._render_all()
            self._dirty = False

    def _render_all(self):
        total=len(self.state.placeholders)
        done=len(self.state.mapeamento)
        self.prog.set(done/max(1,total))
        self.lbl_progress.configure(text=f"{done}/{total} mapeados")
        self._render_ph()
        self._render_docs()
        self._render_map_list()
        self._update_canvas()
        # status labels
        if self.state.placeholder_atual:
            self.lbl_ph_sel.configure(text=f"Campo: {self.state.placeholder_atual}")
        else:
            self.lbl_ph_sel.configure(text="Campo: —")
        if self.state.documento_atual_path:
            self.lbl_doc_sel.configure(text=f"Documento: {os.path.basename(self.state.documento_atual_path)}")
        else:
            self.lbl_doc_sel.configure(text="Documento: —")
        if total==0:
            self.lbl_status.configure(text="Aguardando modelo…")
        elif self._pending_rect:
            self.lbl_status.configure(text=f"Retângulo para '{self._pending_rect['placeholder']}' pronto — clique em SALVAR")
        else:
            self.lbl_status.configure(text=f"{done}/{total} mapeados" + (" • pronto para gerar" if done==total and total>0 else ""))

    def _render_ph(self):
        c=get_colors()
        for w in self.ph_scroll.winfo_children(): w.destroy()
        filtro=self.search_ph.get().lower().strip()
        for ph in self.state.placeholders:
            if filtro and filtro not in ph.lower(): continue
            mapped=ph in self.state.mapeamento
            sel=ph==self.state.placeholder_atual
            if sel:
                bg=c["primary"]; bd=c["primary"]; fg=c["text_on_primary"]
            elif mapped:
                bg=c["success_soft"]; bd=c["success"]; fg=c["success"]
            else:
                bg=c["surface_elevated"]; bd=c["border"]; fg=c["text"]
            row=ctk.CTkFrame(self.ph_scroll, fg_color=bg, corner_radius=8, border_width=1, border_color=bd)
            row.pack(fill="x", pady=2)
            pref="✓" if mapped else "○"
            lbl=ctk.CTkLabel(row, text=f"{pref}  {{{{{ph}}}}}", font=FONTS["body_small"], text_color=fg)
            lbl.pack(side="left", padx=10, pady=6)
            lbl.bind("<Button-1>", lambda e, p=ph: self._select_ph(p))
            row.bind("<Button-1>", lambda e, p=ph: self._select_ph(p))

    def _select_ph(self, ph):
        self.state.placeholder_atual=ph
        self._render_all()
        # se já tem doc selecionado, mostra canvas
        if self.state.documento_atual_path:
            self._load_image()

    def _render_docs(self):
        c=get_colors()
        for w in self.doc_scroll.winfo_children(): w.destroy()
        if not self.state.documentos_anexados:
            ctk.CTkLabel(self.doc_scroll, text="Nenhum documento anexado", font=FONTS["caption"], text_color=c["text_muted"]).pack(pady=16)
            return
        for doc in self.state.documentos_anexados:
            sel=doc['caminho']==self.state.documento_atual_path
            bg=c["success_soft"] if sel else c["surface_elevated"]
            bd=c["success"] if sel else c["border"]
            row=ctk.CTkFrame(self.doc_scroll, fg_color=bg, corner_radius=8, border_width=1, border_color=bd)
            row.pack(fill="x", pady=2)
            iname = "doc" if doc['tipo'] == "pdf" else "image"
            icolor = c["success"] if sel else c["text_muted"]
            ctk.CTkLabel(row, text="", image=get_icon(iname, 16, icolor)).pack(side="left", padx=(10, 2), pady=6)
            lbl=ctk.CTkLabel(row, text=doc['nome'], font=FONTS["body_small"], text_color=c["success"] if sel else c["text"], anchor="w")
            lbl.pack(side="left", padx=(2, 10), pady=6)
            lbl.bind("<Button-1>", lambda e, d=doc: self._select_doc(d))
            row.bind("<Button-1>", lambda e, d=doc: self._select_doc(d))

    def _select_doc(self, doc):
        self.state.documento_atual_path=doc['caminho']
        self.state.documento_tipo=doc['tipo']
        # precisa carregar imagem no canvas
        self._load_image()
        self._render_all()

    def _load_image(self):
        if not self.state.documento_atual_path:
            return
        # acha doc
        for d in self.state.documentos_anexados:
            if d['caminho']==self.state.documento_atual_path:
                self.canvas.set_image(d['imagem_original'])
                break
        self._update_canvas()

    def _update_canvas(self):
        if not self.canvas.imagem_original:
            return
        # fonte única de verdade: state.mapeamento — o lote é um subproduto
        # sincronizado via MapeamentoService._sync_lote
        rects=[]
        for ph, dados in self.state.mapeamento.items():
            if dados['documento_path']==self.state.documento_atual_path:
                rects.append({'x1':dados['x1'],'y1':dados['y1'],'x2':dados['x2'],'y2':dados['y2'],'label':ph})
        def overlay(cv):
            cv.draw_rects(rects)
        self.canvas.set_overlays([overlay])

    # --- ações ---
    def _anexar(self):
        if not self.state.placeholders:
            messagebox.showwarning("Aviso","Carregue um modelo primeiro")
            return
        from anexo_heic import heic_suportado
        from mensagens import mostrar_info_anexos
        if not mostrar_info_anexos(heic_suportado()):
            return
        from preferencias import carregar_preferencias, set_preferencia
        prefs=carregar_preferencias()
        dir_ini=prefs.get('ultimo_diretorio_anexo', os.path.expanduser("~"))
        caminho=filedialog.askopenfilename(filetypes=obter_filetypes_anexo(), initialdir=dir_ini)
        if not caminho: return
        set_preferencia('ultimo_diretorio_anexo', os.path.dirname(caminho))
        ok, msg=self.doc_svc.anexar(caminho)
        if not ok:
            messagebox.showerror("Erro", msg)
        else:
            # auto seleciona se primeiro
            if not self.state.documento_atual_path:
                self.state.documento_atual_path=caminho
                self._load_image()

    def _on_rect(self, x1,y1,x2,y2):
        if not self.state.placeholder_atual:
            messagebox.showwarning("Aviso","Selecione o campo primeiro")
            return
        if not self.state.documento_atual_path:
            messagebox.showwarning("Aviso","Selecione o documento")
            return
        self._pending_rect={'placeholder':self.state.placeholder_atual,'documento_path':self.state.documento_atual_path,'documento_tipo':self.state.documento_tipo,'x1':x1,'y1':y1,'x2':x2,'y2':y2}
        self._render_all()

    def _salvar(self):
        if not self._pending_rect:
            messagebox.showwarning("Aviso","Desenhe um retângulo primeiro")
            return
        r=self._pending_rect
        self.map_svc.adicionar(r['placeholder'], r['documento_path'], r['documento_tipo'], r['x1'],r['y1'],r['x2'],r['y2'])
        self._pending_rect=None
        self._render_all()

    def _remover_doc(self):
        if not self.state.documento_atual_path:
            return
        self.doc_svc.remover_por_path(self.state.documento_atual_path)

    def _limpar(self):
        if messagebox.askyesno("Confirmar","Limpar todo o mapeamento?"):
            self.map_svc.limpar()
            self._pending_rect=None

    def _undo(self):
        ok,msg=self.map_svc.desfazer()
        messagebox.showinfo("Undo" if ok else "Aviso", msg)

    def _export(self):
        if not self.state.mapeamento:
            messagebox.showwarning("Aviso","Nenhum mapeamento")
            return
        caminho=filedialog.asksaveasfilename(title="Exportar", defaultextension=".json", filetypes=[("JSON","*.json")], initialfile="mapeamento.json")
        if not caminho: return
        try:
            self.map_svc.exportar(caminho)
            messagebox.showinfo("Exportado", f"Salvo em {caminho}")
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def _import(self):
        caminho=filedialog.askopenfilename(title="Importar", filetypes=[("JSON","*.json")])
        if not caminho: return
        import json
        try:
            with open(caminho, encoding='utf-8') as f: data=json.load(f)
            if data.get('modelo_path')!=self.state.modelo_path:
                if not messagebox.askyesno("Modelo diferente","Mapeamento de outro modelo. Continuar?"):
                    return
            self.map_svc.importar(caminho, forcar=True)
            messagebox.showinfo("Importado", f"{len(self.state.mapeamento)} campos")
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def _render_map_list(self):
        c=get_colors()
        for w in self.map_scroll.winfo_children(): w.destroy()
        if not self.state.mapeamento and not self.state.lote_fontes:
            ctk.CTkLabel(self.map_scroll, text="Nenhum mapeamento ainda", font=FONTS["caption"], text_color=c["text_muted"]).pack(pady=6)
            return
        for ph, dados in self.state.mapeamento.items():
            row=ctk.CTkFrame(self.map_scroll, fg_color=c["surface_elevated"], corner_radius=8, border_width=1, border_color=c["border"])
            row.pack(fill="x", pady=2, padx=2)
            ctk.CTkLabel(row, text=f"✓ {ph}", font=FONTS["body_small"], text_color=c["success"], width=160, anchor="w").pack(side="left", padx=8, pady=4)
            ctk.CTkLabel(row, text=f"→ {os.path.basename(dados['documento_path'])}", font=FONTS["caption"], text_color=c["text_muted"]).pack(side="left")
            ctk.CTkButton(row, text="", image=get_icon("x", 12, c["danger"]), width=24, height=20, corner_radius=6, fg_color="transparent", hover_color=c["danger_soft"], command=lambda p=ph: self.map_svc.remover_placeholder(p)).pack(side="right", padx=6)
        if self.state.lote_fontes:
            ctk.CTkLabel(self.map_scroll, text=f"LOTE: {len(self.state.lote_fontes)} doc(s)", font=FONTS["caption"], text_color=c["primary"]).pack(anchor="w", pady=(6,2), padx=6)
