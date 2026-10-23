"""
LoteView - gera documentos em lote a partir de uma planilha (.xlsx/.csv).

Uma linha = um documento. Cada linha é preenchida nos placeholders do modelo
conforme o mapeamento coluna -> campo. Erros de uma linha não abortam o lote.
"""
import os
import threading
import tkinter as tk

import customtkinter as ctk

from config import casa_do_usuario
from historico import adicionar_ao_historico
from logger import log_erro, log_info
from preferencias import carregar_preferencias, set_preferencia
from saida import caminho_saida
from services.planilha import dados_da_linha, ler_planilha, sugerir_mapeamento
from ui import messagebox
from ui.components.widgets import card, scroll_frame, section_header
from ui.file_dialog import escolher_arquivo, escolher_pasta
from ui.icons import get as get_icon
from ui.theme import FONTS, get_colors

SEM_COLUNA = "(não usar)"
MAX_PREVIEW_LINHAS = 10


class LoteView(ctk.CTkFrame):
    def __init__(self, parent, state, geracao_service, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.state = state
        self.geracao = geracao_service
        self._dirty = True
        self._cancel = None
        self._running = False
        self._mapa_vars = {}
        self._build()
        self.state.subscribe(self._on_state)
        self._dirty = False

    def mark_dirty(self):
        self._dirty = True

    def refresh_view(self):
        if self._dirty:
            self._rebuild_mapeamento()
            self._dirty = False

    def rebuild_chrome(self):
        pasta = self.ent_pasta.get() if hasattr(self, "ent_pasta") else ""
        padrao = self.ent_padrao.get() if hasattr(self, "ent_padrao") else ""
        organizar = bool(self.chk_data.get()) if hasattr(self, "chk_data") else False
        for w in self.winfo_children():
            w.destroy()
        self._mapa_vars.clear()
        self._build()
        if pasta:
            self.ent_pasta.delete(0, "end")
            self.ent_pasta.insert(0, pasta)
        if padrao:
            self.ent_padrao.delete(0, "end")
            self.ent_padrao.insert(0, padrao)
        if organizar:
            self.chk_data.select()
        self._rebuild_mapeamento()

    def _on_state(self, ev):
        if ev in ("modelo", "modelos"):
            self._dirty = True

    def _build(self):
        c = get_colors()
        hdr = section_header(self, "Lote por planilha",
                             "Cada linha da planilha gera um documento preenchido",
                             icon="folder")
        hdr.pack(fill="x", padx=24, pady=(18, 8))

        # 1) planilha
        self.card_planilha = card(self)
        self.card_planilha.pack(fill="x", padx=24, pady=6)
        topo = ctk.CTkFrame(self.card_planilha, fg_color="transparent")
        topo.pack(fill="x", padx=14, pady=(12, 4))
        ctk.CTkButton(topo, text="Escolher planilha", image=get_icon("folder", 16, c["text_on_primary"]),
                      compound="left", height=36, corner_radius=10, fg_color=c["primary"],
                      hover_color=c["primary_hover"], text_color=c["text_on_primary"],
                      command=self._escolher_planilha).pack(side="left")
        self.lbl_planilha = ctk.CTkLabel(topo, text="Nenhuma planilha carregada",
                                         font=FONTS["caption"], text_color=c["text_muted"])
        self.lbl_planilha.pack(side="left", padx=12)
        self.preview = ctk.CTkTextbox(self.card_planilha, height=72, corner_radius=10,
                                      font=FONTS["mono"], border_width=1,
                                      border_color=c["border"])
        self.preview.pack(fill="x", padx=12, pady=(0, 12))
        self.preview.insert("1.0", "Selecione .xlsx, .csv ou .tsv. A primeira linha deve conter o cabeçalho.")
        self.preview.configure(state="disabled")

        # 2) mapeamento colunas -> campos
        self.card_mapa = card(self)
        self.card_mapa.pack(fill="both", expand=True, padx=24, pady=6)
        ctk.CTkLabel(self.card_mapa, text="Colunas da planilha para cada campo",
                     font=FONTS["h2"], text_color=c["text"]).pack(anchor="w", padx=16, pady=(12, 2))
        ctk.CTkLabel(self.card_mapa, text="Sugestão automática pelo nome do cabeçalho — ajuste se precisar",
                     font=FONTS["caption"], text_color=c["text_faint"]).pack(anchor="w", padx=16, pady=(0, 6))
        self.mapa_scroll = scroll_frame(self.card_mapa, height=170)
        self.mapa_scroll.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self._rebuild_mapeamento()

        # 3) saída + ação
        self.card_acao = card(self)
        self.card_acao.pack(fill="x", padx=24, pady=(6, 14))
        prefs = carregar_preferencias()

        linha = ctk.CTkFrame(self.card_acao, fg_color="transparent")
        linha.pack(fill="x", padx=14, pady=(12, 4))
        ctk.CTkLabel(linha, text="Pasta", font=FONTS["caption"], text_color=c["text_muted"],
                     width=44, anchor="w").pack(side="left")
        self.ent_pasta = ctk.CTkEntry(linha, height=32, font=FONTS["body_small"],
                                       placeholder_text="última pasta usada")
        self.ent_pasta.pack(side="left", fill="x", expand=True, padx=(0, 6))
        if prefs.get("pasta_saida_padrao"):
            self.ent_pasta.insert(0, prefs["pasta_saida_padrao"])
        ctk.CTkButton(linha, text="Escolher", width=84, height=32, corner_radius=8,
                      fg_color=c["surface_elevated"], text_color=c["primary_hover"],
                      border_width=1, border_color=c["border"],
                      command=self._escolher_pasta).pack(side="left")
        self.chk_data = ctk.CTkCheckBox(linha, text="Subpasta por data", font=FONTS["caption"],
                                        text_color=c["text_muted"],
                                        checkbox_width=18, checkbox_height=18)
        self.chk_data.pack(side="left", padx=(12, 2))
        if prefs.get("organizar_por_data"):
            self.chk_data.select()

        linha2 = ctk.CTkFrame(self.card_acao, fg_color="transparent")
        linha2.pack(fill="x", padx=14, pady=(0, 12))
        ctk.CTkLabel(linha2, text="Nome", font=FONTS["caption"], text_color=c["text_muted"],
                     width=44, anchor="w").pack(side="left")
        self.ent_padrao = ctk.CTkEntry(linha2, height=32, font=FONTS["body_small"])
        self.ent_padrao.insert(0, prefs.get("padrao_nome_saida") or "{modelo}_{indice}")
        self.ent_padrao.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.btn_gerar = ctk.CTkButton(linha2, text="Gerar lote", image=get_icon("rocket", 18, c["text_on_primary"]),
                                       compound="left", height=34, corner_radius=10, fg_color=c["success"],
                                       hover_color=c["success_hover"], text_color=c["text_on_primary"],
                                       font=FONTS["h3"], command=self._gerar)
        self.btn_gerar.pack(side="left")
        self.btn_cancelar = ctk.CTkButton(linha2, text="Cancelar", height=34, width=92, corner_radius=10,
                                          fg_color="transparent", border_width=1, border_color=c["danger"],
                                          text_color=c["danger"], command=self._cancelar)
        self.progress = ctk.CTkProgressBar(linha2, height=8, width=120)
        self.progress.set(0)
        self.lbl_status = ctk.CTkLabel(linha2, text="", font=FONTS["caption"],
                                       text_color=c["text_muted"])
        self.lbl_status.pack(side="left", padx=(10, 0))

    # --- planilha ---
    def _escolher_planilha(self):
        caminho = escolher_arquivo(
            self, titulo="Escolher planilha",
            filetypes=[("Planilhas", "*.xlsx *.xlsm *.csv *.tsv"), ("Todos", "*.*")],
            inicial=carregar_preferencias().get("ultimo_diretorio_planilha", casa_do_usuario()),
        )
        if not caminho:
            return
        try:
            colunas, linhas = ler_planilha(caminho)
        except Exception as e:
            messagebox.showerror("Planilha", str(e))
            return
        set_preferencia("ultimo_diretorio_planilha", os.path.dirname(caminho))
        self.state.planilha_path = caminho
        self.state.planilha_colunas = colunas
        self.state.planilha_linhas = linhas
        self.state.planilha_mapeamento = sugerir_mapeamento(colunas, self.state.placeholders)
        self.lbl_planilha.configure(
            text=f"{os.path.basename(caminho)}  •  {len(linhas)} linha(s)  •  {len(colunas)} coluna(s)"
        )
        self._atualizar_preview()
        self._rebuild_mapeamento()

    def _atualizar_preview(self):
        colunas = self.state.planilha_colunas
        linhas = self.state.planilha_linhas[:MAX_PREVIEW_LINHAS]
        if not colunas:
            return
        largura = [max(len(str(colunas[i])), *(len(linha[i]) for linha in linhas)) for i in range(len(colunas))]
        largura = [min(w, 16) for w in largura]

        def fmt(valores):
            celulas = []
            for valor, w in zip(valores, largura, strict=False):
                texto = str(valor)
                if len(texto) > w:
                    texto = texto[: w - 1] + "…"
                celulas.append(texto.ljust(w))
            return " | ".join(celulas)

        texto = [fmt(colunas), "-+-".join("-" * w for w in largura)]
        texto += [fmt(linha) for linha in linhas]
        if len(self.state.planilha_linhas) > MAX_PREVIEW_LINHAS:
            texto.append(f"… (+{len(self.state.planilha_linhas) - MAX_PREVIEW_LINHAS} linha(s))")
        self.preview.configure(state="normal")
        self.preview.delete("1.0", tk.END)
        self.preview.insert("1.0", "\n".join(texto))
        self.preview.configure(state="disabled")

    # --- mapeamento ---
    def _rebuild_mapeamento(self):
        if not hasattr(self, "mapa_scroll") or not self.mapa_scroll.winfo_exists():
            return
        for w in self.mapa_scroll.winfo_children():
            w.destroy()
        self._mapa_vars = {}
        placeholders = list(self.state.placeholders)
        colunas = list(self.state.planilha_colunas)
        c = get_colors()
        if not placeholders:
            ctk.CTkLabel(self.mapa_scroll, text="Carregue um modelo na aba Modelos para ver os campos.",
                         font=FONTS["caption"], text_color=c["text_muted"]).pack(anchor="w", padx=8, pady=6)
            return
        if not colunas:
            ctk.CTkLabel(self.mapa_scroll, text="Escolha uma planilha para mapear as colunas.",
                         font=FONTS["caption"], text_color=c["text_muted"]).pack(anchor="w", padx=8, pady=6)
            return
        sugestoes = self.state.planilha_mapeamento or sugerir_mapeamento(colunas, placeholders)
        valores = [SEM_COLUNA, *colunas]
        metade = (len(placeholders) + 1) // 2
        for grupo in (placeholders[:metade], placeholders[metade:]):
            coluna_ui = ctk.CTkFrame(self.mapa_scroll, fg_color="transparent")
            coluna_ui.pack(side="left", fill="both", expand=True, padx=(2, 6))
            for ph in grupo:
                linha = ctk.CTkFrame(coluna_ui, fg_color=c["surface_hover"], corner_radius=8)
                linha.pack(fill="x", pady=1)
                ctk.CTkLabel(linha, text=f"{{{{{ph}}}}}", font=FONTS["body_small"],
                             text_color=c["text"], width=150, anchor="w").pack(
                    side="left", padx=(10, 4), pady=3)
                var = ctk.StringVar(value=sugestoes.get(ph, SEM_COLUNA))
                ctk.CTkOptionMenu(linha, values=valores, variable=var, width=250, height=26,
                                  font=FONTS["caption"], fg_color=c["surface_elevated"],
                                  button_color=c["primary"], text_color=c["text"],
                                  dropdown_fg_color=c["surface_elevated"],
                                  dropdown_text_color=c["text"]).pack(
                    side="left", padx=(0, 8), pady=3)
                self._mapa_vars[ph] = var

    def _mapeamento_atual(self):
        return {ph: var.get() for ph, var in self._mapa_vars.items() if var.get() != SEM_COLUNA}

    # --- saída ---
    def _escolher_pasta(self):
        inicial = self.ent_pasta.get().strip() or casa_do_usuario()
        pasta = escolher_pasta(self, titulo="Pasta de saída", inicial=inicial)
        if not pasta:
            return
        self.ent_pasta.delete(0, "end")
        self.ent_pasta.insert(0, pasta)

    def _opcoes_saida(self):
        prefs = carregar_preferencias()
        pasta = (self.ent_pasta.get().strip() or prefs.get("pasta_saida_padrao")
                 or prefs.get("ultimo_diretorio_saida", casa_do_usuario()))
        padrao = self.ent_padrao.get().strip() or "{modelo}_{indice}"
        organizar = bool(self.chk_data.get())
        set_preferencia("pasta_saida_padrao", pasta)
        set_preferencia("padrao_nome_saida", padrao)
        set_preferencia("organizar_por_data", organizar)
        return pasta, padrao, organizar

    # --- geração ---
    def _modelos_para_gerar(self):
        if self.state.modelos:
            return list(self.state.modelos)
        if self.state.modelo_path:
            return [{"path": self.state.modelo_path, "tipo": self.state.modelo_tipo,
                     "placeholders": list(self.state.placeholders)}]
        return []

    def _gerar(self):
        if self._running:
            return
        modelos = self._modelos_para_gerar()
        if not modelos:
            messagebox.showwarning("Lote", "Carregue um modelo na aba Modelos.")
            return
        if not self.state.planilha_linhas:
            messagebox.showwarning("Lote", "Escolha uma planilha com linhas de dados.")
            return
        mapa = self._mapeamento_atual()
        if not mapa:
            messagebox.showwarning("Lote", "Mapeie ao menos uma coluna para um campo.")
            return
        pendentes = [ph for ph in self.state.placeholders if ph not in mapa]
        if pendentes and not messagebox.askyesno(
                "Campos sem coluna",
                f"Sem coluna na planilha: {', '.join(pendentes)}\n"
                "Esses campos ficarão vazios. Continuar?"):
            return

        pasta, padrao, organizar = self._opcoes_saida()
        self.state.planilha_mapeamento = dict(mapa)
        self._cancel = threading.Event()
        self._running = True
        self.btn_gerar.configure(state="disabled")
        self.btn_cancelar.pack(side="left", padx=8)
        self.progress.pack(side="left", fill="x", expand=True, padx=8)
        self.progress.set(0)
        total = len(self.state.planilha_linhas)
        self.lbl_status.configure(text=f"Gerando 0/{total}…")

        colunas = list(self.state.planilha_colunas)
        linhas = list(self.state.planilha_linhas)
        cancel = self._cancel

        def run():
            gerados = 0
            erros = []
            for indice, linha in enumerate(linhas, start=1):
                if cancel.is_set():
                    break
                dados = dados_da_linha(colunas, linha, mapa)
                for m in modelos:
                    try:
                        ext = os.path.splitext(m["path"])[1]
                        out = caminho_saida(pasta, padrao, m["path"], dados, extensao=ext,
                                             indice=indice, organizar_por_data=organizar)
                        self.geracao.gerar_um(m["path"], m["tipo"], dados, out)
                        gerados += 1
                        adicionar_ao_historico(m["path"], m["tipo"], out,
                                               len([v for v in dados.values() if v]), dados=dados)
                    except Exception as e:
                        erros.append(f"Linha {indice} — {os.path.basename(m['path'])}: {e}")
                        log_erro(f"Lote linha {indice}: {e}")
                self.after(0, lambda i=indice: self._progresso(i, total))
            return gerados, erros

        def fim(gerados, erros):
            self._running = False
            self.btn_gerar.configure(state="normal")
            self.btn_cancelar.pack_forget()
            self.progress.pack_forget()
            cancelado = cancel.is_set()
            msg = f"{gerados} documento(s) gerado(s)" + (" — cancelado" if cancelado else "")
            self.lbl_status.configure(text=msg)
            log_info(f"Lote: {msg}")
            if erros:
                detalhe = "\n".join(erros[:15])
                if len(erros) > 15:
                    detalhe += f"\n… (+{len(erros) - 15} erro(s))"
                messagebox.showwarning("Lote concluído com erros", f"{msg}\n\n{detalhe}")
            else:
                messagebox.showinfo("Lote concluído", msg)

        def worker():
            gerados, erros = run()
            self.after(0, lambda: fim(gerados, erros))

        t = threading.Thread(target=worker, daemon=True)
        t.start()

    def _progresso(self, atual, total):
        self.progress.set(atual / total if total else 0)
        self.lbl_status.configure(text=f"Gerando {atual}/{total}…")

    def _cancelar(self):
        if self._cancel is not None:
            self._cancel.set()
            self.lbl_status.configure(text="Cancelando após o documento atual…")
