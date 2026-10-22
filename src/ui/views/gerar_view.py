"""
GerarView - preview + edição + geração com threading OCR
"""
import os
import tkinter as tk
from datetime import datetime

import customtkinter as ctk

from config import CONF_BOA, CONF_MEDIA
from fichas import listar_fichas, obter_ficha, salvar_ficha
from historico import adicionar_ao_historico
from logger import log_erro, log_info
from preferencias import carregar_preferencias, set_preferencia
from saida import caminho_saida, renderizar_nome
from ui import messagebox
from ui.components.widgets import card, scroll_frame, section_header, wheel_para_scroll
from ui.file_dialog import escolher_pasta, salvar_arquivo
from ui.icons import get as get_icon
from ui.theme import FONTS, get_colors
from validadores_extra import sugerir_validacao, validar_campo


class GerarView(ctk.CTkFrame):
    def __init__(self, parent, state, extracao_service, geracao_service, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.state = state
        self.extracao = extracao_service
        self.geracao = geracao_service
        self._dirty = True
        self._build()
        self.state.subscribe(self._on_state)
        self._dirty = False

    def mark_dirty(self):
        self._dirty = True

    def refresh_view(self):
        self._refresh_status()

    def rebuild_chrome(self):
        """Reconstrói widgets estáticos (pós-toggle), preservando preview e status."""
        txt = self.text.get("1.0", "end-1c") if hasattr(self, "text") else ""
        status = self.status.cget("text") if hasattr(self, "status") else ""
        for w in self.winfo_children():
            w.destroy()
        self._build()
        if txt:
            self.text.insert("1.0", txt)
        if status:
            self.status.configure(text=status)

    def _build(self):
        c=get_colors()
        hdr=section_header(self, "Gerar Documento", "Extraia via OCR ou preencha manualmente, revise e gere o arquivo final", icon="spark")
        hdr.pack(fill="x", padx=24, pady=(18,8))

        # KPI de prontidão (card tintado)
        kpi_row=ctk.CTkFrame(self, fg_color="transparent")
        kpi_row.pack(fill="x", padx=24, pady=8)
        self.card_pronto=card(kpi_row, fg_color=c["primary_tint"], border_color=c["primary"])
        self.card_pronto.pack(side="left", fill="x", expand=True, padx=6)
        self.lbl_pronto=ctk.CTkLabel(self.card_pronto, text="Aguardando…", font=FONTS["h3"], text_color=c["text"])
        self.lbl_pronto.pack(padx=16, pady=16)

        # preview
        preview=card(self)
        preview.pack(fill="both", expand=True, padx=24, pady=8)
        ctk.CTkLabel(preview, text="Dados extraídos", font=FONTS["h2"], text_color=c["text"]).pack(anchor="w", padx=16, pady=(14,6))
        self.text = ctk.CTkTextbox(preview, height=180, corner_radius=12, font=FONTS["body_small"], border_width=1, border_color=c["border"])
        self.text.pack(fill="both", expand=True, padx=12, pady=(0,12))

        # actions
        actions=ctk.CTkFrame(self, fg_color="transparent")
        actions.pack(fill="x", padx=24, pady=8)
        ctk.CTkButton(actions, text="Extrair e Editar", image=get_icon("search", 18, c["text_on_primary"]), compound="left", height=44, corner_radius=12, fg_color=c["primary"], hover_color=c["primary_hover"], text_color=c["text_on_primary"], font=FONTS["h3"], command=self._extrair).pack(side="left", expand=True, fill="x", padx=6)
        ctk.CTkButton(actions, text="Preencher manual", image=get_icon("edit", 18, c["primary_hover"]), compound="left", height=44, corner_radius=12, fg_color=c["surface_elevated"], text_color=c["primary_hover"], border_width=1, border_color=c["primary"], command=self._preencher_manual).pack(side="left", expand=True, fill="x", padx=6)
        ctk.CTkButton(actions, text="Gerar", image=get_icon("rocket", 18, c["text_on_primary"]), compound="left", height=44, corner_radius=12, fg_color=c["success"], hover_color=c["success_hover"], text_color=c["text_on_primary"], font=("Inter",13,"bold"), command=self._gerar).pack(side="left", expand=True, fill="x", padx=6)

        self._build_saida(self)
        self.status=ctk.CTkLabel(self, text="Dica: mapeie todos os campos para melhor resultado", font=FONTS["caption"], text_color=c["text_muted"])
        self.status.pack(fill="x", padx=24, pady=(0,12))
        self._refresh_status()

    def _build_saida(self, parent):
        """Opções de pasta e padrão de nome da saída (Fase 2)."""
        c=get_colors()
        prefs=carregar_preferencias()
        box=card(parent)
        box.pack(fill="x", padx=24, pady=(0,8))
        ctk.CTkLabel(box, text="Saída", font=FONTS["h2"], text_color=c["text"]).pack(anchor="w", padx=16, pady=(12,4))

        linha1=ctk.CTkFrame(box, fg_color="transparent")
        linha1.pack(fill="x", padx=12, pady=2)
        ctk.CTkLabel(linha1, text="Pasta", font=FONTS["caption"], text_color=c["text_muted"], width=52, anchor="w").pack(side="left")
        self.ent_pasta=ctk.CTkEntry(linha1, height=32, font=FONTS["body_small"], placeholder_text="última pasta usada")
        self.ent_pasta.pack(side="left", fill="x", expand=True, padx=(0,6))
        pasta_atual=prefs.get('pasta_saida_padrao') or ""
        if pasta_atual:
            self.ent_pasta.insert(0, pasta_atual)
        ctk.CTkButton(linha1, text="Escolher", width=90, height=32, corner_radius=8,
                      fg_color=c["surface_elevated"], text_color=c["primary_hover"], border_width=1,
                      border_color=c["border"], command=self._escolher_pasta).pack(side="left")

        linha2=ctk.CTkFrame(box, fg_color="transparent")
        linha2.pack(fill="x", padx=12, pady=(4,2))
        ctk.CTkLabel(linha2, text="Nome", font=FONTS["caption"], text_color=c["text_muted"], width=52, anchor="w").pack(side="left")
        self.ent_padrao=ctk.CTkEntry(linha2, height=32, font=FONTS["body_small"])
        self.ent_padrao.pack(side="left", fill="x", expand=True)
        self.ent_padrao.insert(0, prefs.get('padrao_nome_saida') or "{modelo}")

        ctk.CTkLabel(box, text="tokens: {modelo} {data} {hora} {indice}  •  campos: {{nome}}", font=FONTS["caption"], text_color=c["text_faint"]).pack(anchor="w", padx=16, pady=(0,2))

        self.chk_data=ctk.CTkCheckBox(box, text="Criar subpasta por data (AAAA-MM-DD)", font=FONTS["caption"], text_color=c["text_muted"], checkbox_width=18, checkbox_height=18)
        self.chk_data.pack(anchor="w", padx=16, pady=(2,4))
        if prefs.get('organizar_por_data'):
            self.chk_data.select()

        self.chk_preview=ctk.CTkCheckBox(box, text="Abrir pré-visualização depois de gerar", font=FONTS["caption"], text_color=c["text_muted"], checkbox_width=18, checkbox_height=18)
        self.chk_preview.pack(anchor="w", padx=16, pady=(0,12))
        if prefs.get('preview_apos_gerar'):
            self.chk_preview.select()

    def _escolher_pasta(self):
        inicial=self.ent_pasta.get().strip() or carregar_preferencias().get('ultimo_diretorio_saida', "~")
        pasta=escolher_pasta(self, titulo="Pasta de saída", inicial=inicial)
        if not pasta:
            return
        self.ent_pasta.delete(0, "end")
        self.ent_pasta.insert(0, pasta)

    def _opcoes_saida(self):
        """Lê e persiste as opções de saída. Retorna (pasta, padrao, organizar)."""
        prefs=carregar_preferencias()
        pasta=self.ent_pasta.get().strip() or prefs.get('pasta_saida_padrao') or prefs.get('ultimo_diretorio_saida', os.path.expanduser("~"))
        padrao=self.ent_padrao.get().strip() or "{modelo}"
        organizar=bool(self.chk_data.get())
        set_preferencia('pasta_saida_padrao', pasta)
        set_preferencia('padrao_nome_saida', padrao)
        set_preferencia('organizar_por_data', organizar)
        set_preferencia('preview_apos_gerar', bool(self.chk_preview.get()))
        return pasta, padrao, organizar

    def _on_state(self, ev):
        if ev in ("mapeamento","modelo","backup"):
            self._refresh_status()
            self._dirty = False

    def _refresh_status(self):
        total=len(self.state.placeholders)
        mapped=len(self.state.mapeamento)
        if total==0:
            self.lbl_pronto.configure(text="Nenhum modelo")
        elif mapped==total:
            self.lbl_pronto.configure(text=f"Pronto para gerar  •  {mapped}/{total} mapeados", text_color=get_colors()["success_hover"])
        elif mapped>0:
            self.lbl_pronto.configure(text=f"{mapped}/{total} mapeados — falta mapear", text_color=get_colors()["warning"])
        else:
            self.lbl_pronto.configure(text="Nenhum mapeamento", text_color=get_colors()["text_muted"])

    def _extrair(self):
        if not self.state.mapeamento:
            messagebox.showwarning("Aviso","Nenhum mapeamento")
            return
        pend=[ph for ph in self.state.placeholders if ph not in self.state.mapeamento]
        if pend:
            if not messagebox.askyesno("Aviso", f"Campos não mapeados: {', '.join(pend)}\nContinuar? (ficarão vazios)"):
                return
        # loading overlay
        dlg=ctk.CTkToplevel(self)
        dlg.title("Extraindo…")
        dlg.geometry("360x140")
        dlg.transient(self.winfo_toplevel()); dlg.grab_set()
        c=get_colors()
        top = ctk.CTkFrame(dlg, fg_color="transparent")
        top.pack(pady=12)
        ctk.CTkLabel(top, text="", image=get_icon("search", 20, c["text"])).pack(side="left", padx=(0, 8))
        ctk.CTkLabel(top, text="Extraindo com OCR…", font=FONTS["h2"]).pack(side="left")
        prog=ctk.CTkProgressBar(dlg, width=300)
        prog.pack(pady=6); prog.set(0)
        lbl=ctk.CTkLabel(dlg, text="0%", font=FONTS["caption"], text_color=c["text_muted"])
        lbl.pack()
        def on_prog(cur, tot, ph):
            prog.set(cur/tot)
            lbl.configure(text=f"{cur}/{tot} — {ph}")
        def on_done(dados, conf):
            dlg.destroy()
            self.state.confianca_ocr = conf
            self._abrir_edicao(dados, conf)
        def on_err(ph, e): log_erro(f"OCR {ph}: {e}")
        marshal=lambda fn: self.after(0, fn)
        self.extracao.extrair_todos(on_progress=on_prog, on_done=lambda d, c: self.after(0, lambda: on_done(d, c)), on_error=on_err, marshal=marshal)

    def _preencher_manual(self):
        if not self.state.placeholders:
            messagebox.showwarning("Aviso","Carregue um modelo")
            return
        dados={ph: self.state.dados_extraidos.get(ph,"") for ph in self.state.placeholders}
        self._abrir_edicao(dados)

    def _cor_confianca(self, ph):
        """Cor do selo por confiança: None = sem OCR; 0.0 após OCR = vazio."""
        conf = self.state.confianca_ocr.get(ph)
        if conf is None:
            return None
        c = get_colors()
        if conf <= 0.0:
            return c["danger"]
        if conf < CONF_MEDIA:
            return c["danger"]
        if conf < CONF_BOA:
            return c["warning"]
        return c["success"]

    def _selo_confianca(self, parent, ph):
        """Label de confiança (ou None quando não houve OCR)."""
        conf = self.state.confianca_ocr.get(ph)
        if conf is None:
            return None
        c = get_colors()
        if conf <= 0.0:
            txt, cor = "OCR: campo vazio", c["danger"]
        elif conf < CONF_MEDIA:
            txt, cor = f"OCR: confiança baixa ({conf:.0f}%)", c["danger"]
        elif conf < CONF_BOA:
            txt, cor = f"OCR: confiança média ({conf:.0f}%)", c["warning"]
        else:
            txt, cor = f"OCR: confiança boa ({conf:.0f}%)", c["success"]
        return ctk.CTkLabel(parent, text=txt, font=FONTS["caption"], text_color=cor)

    def _abrir_edicao(self, dados_temp, conf_temp=None):
        c=get_colors()
        win=ctk.CTkToplevel(self)
        win.title("Revisar dados")
        win.geometry("720x620")
        win.transient(self.winfo_toplevel()); win.grab_set()
        ctk.CTkLabel(win, text="Revise e corrija", font=FONTS["h1"]).pack(pady=(12,2))
        ctk.CTkLabel(win, text="Correções se aplicam a todas as ocorrências do campo", font=FONTS["caption"], text_color=c["text_muted"]).pack()

        barra_ficha=ctk.CTkFrame(win, fg_color="transparent")
        barra_ficha.pack(fill="x", padx=16, pady=(8,0))
        ctk.CTkLabel(barra_ficha, text="Ficha", font=FONTS["caption"], text_color=c["text_muted"]).pack(side="left")
        fichas_disp=listar_fichas()
        self._combo_ficha=ctk.CTkComboBox(barra_ficha, values=fichas_disp or ["(nenhuma)"], width=200, height=30, font=FONTS["caption"])
        self._combo_ficha.pack(side="left", padx=8)
        if fichas_disp:
            self._combo_ficha.set(fichas_disp[0])
        ctk.CTkButton(barra_ficha, text="Aplicar", width=80, height=30, corner_radius=8, fg_color=c["surface_elevated"], text_color=c["primary_hover"], border_width=1, border_color=c["border"], command=lambda: aplicar_ficha()).pack(side="left", padx=4)

        scroll=scroll_frame(win, height=380)
        scroll.pack(fill="both", expand=True, padx=16, pady=10)
        entries={}
        baixos=[]
        if conf_temp is not None:
            self.state.confianca_ocr = conf_temp
        for ph, val in dados_temp.items():
            cor=self._cor_confianca(ph)
            f=ctk.CTkFrame(scroll, fg_color=c["surface_elevated"], corner_radius=10, border_width=1, border_color=cor or c["border"])
            f.pack(fill="x", pady=4)
            top=ctk.CTkFrame(f, fg_color="transparent")
            top.pack(fill="x", padx=12, pady=(8,2))
            ctk.CTkLabel(top, text=f"{{{{{ph}}}}}", font=FONTS["h3"], text_color=c["text"]).pack(side="left")
            selo=self._selo_confianca(top, ph)
            if selo: selo.pack(side="right")
            if cor in (c["danger"], c["warning"]):
                baixos.append(ph)
            e=ctk.CTkTextbox(f, height=50, font=FONTS["body_small"])
            e.insert("1.0", val)
            e.pack(fill="x", padx=10, pady=(0,4))
            wheel_para_scroll(scroll, e)
            entries[ph]=e
            tipo=sugerir_validacao(ph.lower())
            if tipo:
                ctk.CTkLabel(f, text=f"validação: {tipo}", font=FONTS["caption"], text_color=c["text_faint"]).pack(anchor="w", padx=12, pady=(0,6))
        originais=dict(dados_temp)

        def aplicar_ficha():
            nome=self._combo_ficha.get()
            dados_ficha=obter_ficha(nome)
            if not dados_ficha:
                messagebox.showinfo("Fichas", "Selecione uma ficha salva.", parent=win)
                return
            aplicados=0
            for ph, ent in entries.items():
                if ph in dados_ficha:
                    ent.delete("1.0", tk.END)
                    ent.insert("1.0", dados_ficha[ph])
                    aplicados+=1
            self.status.configure(text=f"Ficha '{nome}' aplicada ({aplicados} campo(s)) — revise e confirme")

        def salvar_ficha_ui():
            nome=messagebox.pedir_texto("Salvar ficha", "Nome da ficha (ex.: nome do cliente):", parent=win)
            if not nome:
                return
            atuais={ph: ent.get("1.0", tk.END).strip() for ph, ent in entries.items()}
            ok, msg=salvar_ficha(nome, atuais)
            if ok:
                valores=listar_fichas()
                self._combo_ficha.configure(values=valores)
                self._combo_ficha.set(nome)
            messagebox.showinfo("Fichas", msg, parent=win)

        ctk.CTkButton(barra_ficha, text="Salvar ficha", width=110, height=30, corner_radius=8,
                      fg_color=c["primary"], hover_color=c["primary_hover"], text_color=c["text_on_primary"],
                      command=salvar_ficha_ui).pack(side="left", padx=4)
        if baixos:
            ctk.CTkLabel(scroll, text=f"Revisar com atenção: {', '.join(baixos)}", font=FONTS["caption"], text_color=c["warning"], justify="left").pack(anchor="w", padx=12, pady=(8, 2))
        def confirmar():
            erros=[]
            novos={}
            for ph, ent in entries.items():
                txt=ent.get("1.0", tk.END).strip()
                novos[ph]=txt
                # valor alterado manualmente: a confiança do OCR não vale mais
                if txt != originais.get(ph, ""):
                    self.state.confianca_ocr.pop(ph, None)
                if txt:
                    ok,msg=validar_campo(ph, txt)
                    if not ok: erros.append(f"{ph}: {msg}")
            if erros and messagebox.askyesno("Validação", "Erros:\n"+"\n".join(erros)+"\n\nCorrigir?"):
                return
            self.state.dados_extraidos=novos
            win.destroy()
            self.text.delete("1.0", tk.END)
            for k,v in novos.items():
                self.text.insert(tk.END, f"{k}:\n  {v}\n\n")
            self.status.configure(text="Dados revisados — clique em Gerar")
        bar=ctk.CTkFrame(win, fg_color="transparent")
        bar.pack(pady=10)
        ctk.CTkButton(bar, text="Confirmar", image=get_icon("check", 16, get_colors()["text_on_primary"]), compound="left", command=confirmar, fg_color=get_colors()["success"], hover_color=get_colors()["success_hover"], corner_radius=10, height=38).pack(side="left", padx=6)
        ctk.CTkButton(bar, text="Cancelar", command=win.destroy, fg_color="transparent", border_width=1, border_color=c["border"], text_color=c["text"], corner_radius=10, height=38).pack(side="left", padx=6)

    def _gerar(self):
        if not self.state.dados_extraidos:
            messagebox.showwarning("Aviso","Extraia/Preencha primeiro")
            return
        if not self.state.modelo_path and not self.state.modelos:
            messagebox.showwarning("Aviso","Carregue um modelo")
            return
        pasta_padrao, padrao, organizar = self._opcoes_saida()
        modelos=self.state.modelos if self.state.modelos else [{'path':self.state.modelo_path,'tipo':self.state.modelo_tipo,'placeholders':self.state.placeholders}]
        tem_lote=bool(self.state.lote_fontes)
        if len(modelos)==1 and not tem_lote:
            m=modelos[0]
            dados={ph: self.state.dados_extraidos.get(ph,"") for ph in m['placeholders']}
            ext=os.path.splitext(m['path'])[1]
            inicialdir=pasta_padrao
            if organizar:
                inicialdir=os.path.join(pasta_padrao, datetime.now().strftime("%Y-%m-%d"))
                os.makedirs(inicialdir, exist_ok=True)
            out=salvar_arquivo(self, titulo="Salvar documento", defaultextension=ext, filetypes=[(ext.upper().replace('.',''), f"*{ext}")], nome_inicial=f"{renderizar_nome(padrao, m['path'], dados)}{ext}", inicial=inicialdir)
            if not out: return
            set_preferencia('ultimo_diretorio_saida', os.path.dirname(out))
            try:
                self.geracao.gerar_um(m['path'], m['tipo'], dados, out)
                messagebox.showinfo("Sucesso", f"Documento gerado:\n{out}")
                adicionar_ao_historico(m['path'], m['tipo'], out, len([v for v in dados.values() if v]), dados=dados)
                self.status.configure(text=f"Salvo: {os.path.basename(out)}")
                log_info(f"Gerado: {out}")
                if self.chk_preview.get():
                    self._abrir_preview(out)
            except Exception as e:
                messagebox.showerror("Erro", str(e)); log_erro(str(e))
            return
        pasta=escolher_pasta(self, titulo="Selecione pasta de saída", inicial=pasta_padrao)
        if not pasta: return
        set_preferencia('ultimo_diretorio_saida', pasta)
        fontes=self.state.lote_fontes if tem_lote else [None]
        total_jobs=len(fontes)*len(modelos)
        padrao_efetivo = padrao
        if tem_lote and padrao == "{modelo}":
            padrao_efetivo = "{modelo}_{indice}"

        primeira=[None]

        def run():
            proc=0; errs=[]
            for idx, fonte in enumerate(fontes, start=1):
                dados_fonte=self.extracao.extrair_de_fonte(fonte) if tem_lote else self.state.dados_extraidos
                for m in modelos:
                    dados={ph: dados_fonte.get(ph,"") for ph in m['placeholders']}
                    try:
                        ext=os.path.splitext(m['path'])[1]
                        out=caminho_saida(pasta, padrao_efetivo, m['path'], dados, extensao=ext,
                                          indice=idx if tem_lote else None,
                                          organizar_por_data=organizar)
                        self.geracao.gerar_um(m['path'], m['tipo'], dados, out)
                        proc+=1
                        if primeira[0] is None:
                            primeira[0]=out
                        adicionar_ao_historico(m['path'], m['tipo'], out, len([v for v in dados.values() if v]), dados=dados)
                    except Exception as e:
                        errs.append(f"{os.path.basename(m['path'])}: {e}")
            return proc, errs

        def done(proc, errs):
            msg=f"Concluído! {proc} documento(s)"
            if errs: msg+="\nErros:\n"+"\n".join(errs)
            messagebox.showinfo("Geração", msg)
            self.status.configure(text=f"{proc} gerado(s)")
            if self.chk_preview.get() and primeira[0]:
                self._abrir_preview(primeira[0])

        # geração em thread: OCR/processamento fora da main thread, tudo o que
        # toca Tk volta marshallizado via after(0, ...)
        import threading
        def worker():
            resultado=run()
            self.after(0, lambda: done(*resultado))
        t=threading.Thread(target=worker, daemon=True)
        t.start()

    def _abrir_preview(self, arquivo):
        """Janela com as primeiras páginas do documento gerado (Fase 5)."""
        c=get_colors()
        win=ctk.CTkToplevel(self)
        win.title(f"Pré-visualização — {os.path.basename(arquivo)}")
        win.geometry("780x840")
        win.transient(self.winfo_toplevel())
        lbl=ctk.CTkLabel(win, text="Convertendo com LibreOffice…", font=FONTS["body"], text_color=c["text_muted"])
        lbl.pack(pady=24)
        refs=[]

        def mostrar(caminhos):
            if not win.winfo_exists():
                return
            lbl.destroy()
            from PIL import Image
            scroll=scroll_frame(win, height=700)
            scroll.pack(fill="both", expand=True, padx=10, pady=(10,4))
            for caminho in caminhos:
                try:
                    img=Image.open(caminho)
                    largura_px, altura_px=img.size
                    largura=min(720, largura_px)
                    foto=ctk.CTkImage(light_image=img, dark_image=img,
                                      size=(largura, max(1, int(altura_px*largura/largura_px))))
                    refs.append(foto)
                    ctk.CTkLabel(scroll, text="", image=foto).pack(pady=6)
                except Exception as e:
                    log_erro(f"Preview: {e}")
            ctk.CTkButton(win, text="Fechar", width=120, height=36, corner_radius=10,
                          fg_color=c["surface_elevated"], text_color=c["text"],
                          border_width=1, border_color=c["border"],
                          command=win.destroy).pack(pady=(4,12))
            win._refs_preview=refs

        def erro(mensagem):
            if not win.winfo_exists():
                return
            lbl.configure(text=f"Não foi possível pré-visualizar.\n{mensagem}", text_color=c["danger"])
            ctk.CTkButton(win, text="Fechar", width=120, height=36, corner_radius=10,
                          fg_color=c["surface_elevated"], text_color=c["text"],
                          border_width=1, border_color=c["border"],
                          command=win.destroy).pack(pady=12)

        def run():
            try:
                from preview import renderizar
                caminhos=renderizar(arquivo, max_paginas=3)
                self.after(0, lambda: mostrar(caminhos))
            except Exception as e:
                log_erro(f"Preview: {e}")
                self.after(0, lambda msg=str(e): erro(msg))

        import threading
        threading.Thread(target=run, daemon=True).start()
