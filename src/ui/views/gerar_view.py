"""
GerarView - preview + edição + geração com threading OCR
"""
import os
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk

from historico import adicionar_ao_historico
from logger import log_erro, log_info
from preferencias import carregar_preferencias, set_preferencia
from ui.components.widgets import card, section_header
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

        self.status=ctk.CTkLabel(self, text="Dica: mapeie todos os campos para melhor resultado", font=FONTS["caption"], text_color=c["text_muted"])
        self.status.pack(fill="x", padx=24, pady=(0,12))
        self._refresh_status()

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
        def on_done(dados):
            dlg.destroy()
            self._abrir_edicao(dados)
        def on_err(ph, e): log_erro(f"OCR {ph}: {e}")
        marshal=lambda fn: self.after(0, fn)
        self.extracao.extrair_todos(on_progress=on_prog, on_done=lambda d: self.after(0, lambda: on_done(d)), on_error=on_err, marshal=marshal)

    def _preencher_manual(self):
        if not self.state.placeholders:
            messagebox.showwarning("Aviso","Carregue um modelo")
            return
        dados={ph: self.state.dados_extraidos.get(ph,"") for ph in self.state.placeholders}
        self._abrir_edicao(dados)

    def _abrir_edicao(self, dados_temp):
        c=get_colors()
        win=ctk.CTkToplevel(self)
        win.title("Revisar dados")
        win.geometry("720x620")
        win.transient(self.winfo_toplevel()); win.grab_set()
        ctk.CTkLabel(win, text="Revise e corrija", font=FONTS["h1"]).pack(pady=(12,2))
        ctk.CTkLabel(win, text="Correções se aplicam a todas as ocorrências do campo", font=FONTS["caption"], text_color=c["text_muted"]).pack()
        scroll=ctk.CTkScrollableFrame(win, height=420)
        scroll.pack(fill="both", expand=True, padx=16, pady=10)
        entries={}
        for ph, val in dados_temp.items():
            f=ctk.CTkFrame(scroll, fg_color=c["surface_elevated"], corner_radius=10, border_width=1, border_color=c["border"])
            f.pack(fill="x", pady=4)
            ctk.CTkLabel(f, text=f"{{{{{ph}}}}}", font=FONTS["h3"]).pack(anchor="w", padx=12, pady=(8,2))
            e=ctk.CTkTextbox(f, height=50, font=FONTS["body_small"])
            e.insert("1.0", val)
            e.pack(fill="x", padx=10, pady=(0,4))
            entries[ph]=e
            tipo=sugerir_validacao(ph.lower())
            if tipo:
                ctk.CTkLabel(f, text=f"validação: {tipo}", font=FONTS["caption"], text_color=c["text_faint"]).pack(anchor="w", padx=12, pady=(0,6))
        def confirmar():
            erros=[]
            novos={}
            for ph, ent in entries.items():
                txt=ent.get("1.0", tk.END).strip()
                novos[ph]=txt
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
        modelos=self.state.modelos if self.state.modelos else [{'path':self.state.modelo_path,'tipo':self.state.modelo_tipo,'placeholders':self.state.placeholders}]
        tem_lote=bool(self.state.lote_fontes)
        if len(modelos)==1 and not tem_lote:
            m=modelos[0]
            dados={ph: self.state.dados_extraidos.get(ph,"") for ph in m['placeholders']}
            ext=os.path.splitext(m['path'])[1]
            out=filedialog.asksaveasfilename(defaultextension=ext, filetypes=[(ext.upper().replace('.',''), f"*{ext}")], initialfile=os.path.basename(m['path']), initialdir=carregar_preferencias().get('ultimo_diretorio_saida', os.path.expanduser("~")))
            if not out: return
            set_preferencia('ultimo_diretorio_saida', os.path.dirname(out))
            try:
                self.geracao.gerar_um(m['path'], m['tipo'], dados, out)
                messagebox.showinfo("Sucesso", f"Documento gerado:\n{out}")
                adicionar_ao_historico(m['path'], m['tipo'], out, len([v for v in dados.values() if v]))
                self.status.configure(text=f"Salvo: {os.path.basename(out)}")
                log_info(f"Gerado: {out}")
            except Exception as e:
                messagebox.showerror("Erro", str(e)); log_erro(str(e))
            return
        pasta=filedialog.askdirectory(title="Selecione pasta de saída")
        if not pasta: return
        fontes=self.state.lote_fontes if tem_lote else [None]
        total_jobs=len(fontes)*len(modelos)

        def run():
            proc=0; errs=[]
            for fonte in fontes:
                dados_fonte=self.extracao.extrair_de_fonte(fonte) if tem_lote else self.state.dados_extraidos
                for m in modelos:
                    dados={ph: dados_fonte.get(ph,"") for ph in m['placeholders']}
                    try:
                        ext=os.path.splitext(m['path'])[1]
                        base=os.path.splitext(os.path.basename(m['path']))[0]
                        if tem_lote:
                            fonte_nome=os.path.splitext(os.path.basename(fonte['documento_path']))[0]
                            out=os.path.join(pasta, f"{base}_{fonte_nome}{ext}")
                        else:
                            out=os.path.join(pasta, f"{base}{ext}")
                        self.geracao.gerar_um(m['path'], m['tipo'], dados, out)
                        proc+=1
                        adicionar_ao_historico(m['path'], m['tipo'], out, len([v for v in dados.values() if v]))
                    except Exception as e:
                        errs.append(f"{os.path.basename(m['path'])}: {e}")
            return proc, errs

        def done(proc, errs):
            msg=f"Concluído! {proc} documento(s)"
            if errs: msg+="\nErros:\n"+"\n".join(errs)
            messagebox.showinfo("Geração", msg)
            self.status.configure(text=f"{proc} gerado(s)")

        # geração em thread: OCR/processamento fora da main thread, tudo o que
        # toca Tk volta marshallizado via after(0, ...)
        import threading
        t=threading.Thread(target=lambda: self.after(0, lambda: done(*run())), daemon=True)
        t.start()
