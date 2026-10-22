"""
Seletor de arquivos/pastas nativo do app (CustomTkinter).

Substitui os diálogos do Tk, que ignoram o tema e destoam do layout.
Arquivos e pastas iniciados por "." ficam ocultos por padrão.

Funções públicas (bloqueiam até o usuário confirmar):
    escolher_arquivo(parent, titulo, filetypes, inicial)
    escolher_arquivos(parent, titulo, filetypes, inicial)
    escolher_pasta(parent, titulo, inicial)
    salvar_arquivo(parent, titulo, filetypes, inicial, nome_inicial, defaultextension)
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime

import customtkinter as ctk

from ui.components.widgets import scroll_frame
from ui.icons import get as get_icon
from ui.theme import FONTS, get_colors

TODOS = "Todos os arquivos"


@dataclass(frozen=True)
class Entrada:
    nome: str
    caminho: str
    eh_dir: bool
    tamanho: int = 0
    modificado: float = 0.0


def sufixos_dos_filetypes(filetypes) -> tuple[str, ...]:
    """Extrai sufixos ('.pdf', ...) de filetypes do Tk. Vazio = todos."""
    sufixos: list[str] = []
    for _rotulo, padroes in filetypes or ():
        for padrao in str(padroes).split():
            if padrao in ("*", "*.*"):
                return ()
            if padrao.startswith("*.") and len(padrao) > 2:
                sufixos.append(padrao[1:].lower())
    return tuple(dict.fromkeys(sufixos))


def _rotulos(filetypes) -> list[str]:
    return [rotulo for rotulo, _p in (filetypes or ())]


def _sufixos_do_rotulo(filetypes, rotulo: str) -> tuple[str, ...]:
    for nome, padroes in filetypes or ():
        if nome == rotulo:
            return sufixos_dos_filetypes([(nome, padroes)])
    return ()


def listar(diretorio, sufixos=(), incluir_ocultos=False, somente_diretorios=False) -> list[Entrada]:
    """Lista o diretório: pastas primeiro, depois arquivos, ambos A-Z.

    Nomes iniciados por "." são omitidos, a menos que incluir_ocultos.
    """
    itens: list[Entrada] = []
    try:
        with os.scandir(diretorio) as it:
            for item in it:
                if not incluir_ocultos and item.name.startswith("."):
                    continue
                try:
                    eh_dir = item.is_dir()
                except OSError:
                    continue
                if eh_dir:
                    itens.append(Entrada(item.name, item.path, True))
                    continue
                if somente_diretorios:
                    continue
                if sufixos and not item.name.lower().endswith(tuple(sufixos)):
                    continue
                try:
                    info = item.stat()
                except OSError:
                    tamanho, modificado = 0, 0.0
                else:
                    tamanho, modificado = info.st_size, info.st_mtime
                itens.append(Entrada(item.name, item.path, False, tamanho, modificado))
    except OSError:
        return []
    itens.sort(key=lambda e: (not e.eh_dir, e.nome.casefold()))
    return itens


def formatar_tamanho(bytes_: int) -> str:
    if bytes_ < 1024:
        return f"{bytes_} B"
    valor = float(bytes_)
    for unidade in ("KB", "MB", "GB", "TB"):
        valor /= 1024
        if valor < 1024:
            return f"{valor:.1f} {unidade}".replace(".0 ", " ")
    return f"{valor:.1f} PB"


def formatar_data(timestamp: float) -> str:
    if not timestamp:
        return ""
    return datetime.fromtimestamp(timestamp).strftime("%d/%m/%Y %H:%M")


def locais_rapidos() -> list[tuple[str, str, str]]:
    """(rótulo, ícone, caminho) dos locais existentes do usuário."""
    casa = os.path.expanduser("~")
    candidatos = [
        ("Início", "inbox", casa),
        ("Documentos", "library", os.path.join(casa, "Documentos")),
        ("Downloads", "save", os.path.join(casa, "Downloads")),
        ("Imagens", "image", os.path.join(casa, "Imagens")),
        ("Área de Trabalho", "folder", os.path.join(casa, "Área de Trabalho")),
        ("Área de Trabalho", "folder", os.path.join(casa, "Desktop")),
    ]
    vistos: set[str] = set()
    locais = []
    for rotulo, icone, caminho in candidatos:
        if caminho in vistos or rotulo in vistos or not os.path.isdir(caminho):
            continue
        vistos.update((caminho, rotulo))
        locais.append((rotulo, icone, caminho))
    return locais


class SeletorArquivos(ctk.CTkToplevel):
    def __init__(self, parent, *, titulo: str, inicial: str | None = None,
                 filetypes=None, multiplo: bool = False, modo: str = "abrir",
                 nome_inicial: str = "", defaultextension: str = ""):
        raiz = _raiz(parent)
        super().__init__(raiz)
        self._modo = modo
        self._multiplo = multiplo
        self._filetypes = list(filetypes or ())
        self._nome_inicial = nome_inicial
        self._defaultextension = defaultextension
        self.resultado = None
        self._selecionados: list[str] = []
        self._entradas: list[Entrada] = []
        self._rotulo_filtro = self._filetypes[0][0] if self._filetypes else TODOS
        self._linhas: dict[str, ctk.CTkFrame] = {}

        c = get_colors()
        self.title(titulo or ("Escolher pasta" if modo == "pasta" else "Escolher arquivo"))
        self.configure(fg_color=c["bg"])
        self.geometry("940x600")
        self.minsize(760, 480)
        self.transient(raiz)
        self.protocol("WM_DELETE_WINDOW", self._cancelar)

        self.diretorio = self._diretorio_inicial(inicial)
        self._build(titulo)
        self._navegar(self.diretorio)
        self.bind("<Escape>", lambda _e: self._cancelar())
        self.bind("<Return>", lambda _e: self._confirmar())
        self.after(60, self._centralizar)
        self.wait_visibility()
        self.grab_set()
        self.after(120, lambda: self.ent_caminho.focus_set())

    # --- layout ---
    def _build(self, titulo):
        c = get_colors()
        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", padx=22, pady=(16, 8))
        icone = "folder" if self._modo == "pasta" else (
            "save" if self._modo == "salvar" else "doc")
        ctk.CTkLabel(head, text="", image=get_icon(icone, 26, c["primary"]),
                     width=30).pack(side="left", padx=(0, 10))
        textos = ctk.CTkFrame(head, fg_color="transparent")
        textos.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(textos, text=titulo or "Selecionar", font=FONTS["h1"],
                     text_color=c["text"]).pack(anchor="w")
        self.lbl_sub = ctk.CTkLabel(textos, text="", font=FONTS["caption"],
                                    text_color=c["text_muted"])
        self.lbl_sub.pack(anchor="w")

        corpo = ctk.CTkFrame(self, fg_color="transparent")
        corpo.pack(fill="both", expand=True, padx=18, pady=(0, 8))

        self._sidebar(corpo)
        self._conteudo(corpo)

    def _sidebar(self, parent):
        c = get_colors()
        barra = ctk.CTkFrame(parent, fg_color=c["surface_elevated"], corner_radius=14,
                             border_width=1, border_color=c["border"], width=190)
        barra.pack(side="left", fill="y", padx=(0, 12), pady=2)
        barra.pack_propagate(False)
        ctk.CTkLabel(barra, text="Locais", font=FONTS["caption"],
                     text_color=c["text_faint"]).pack(anchor="w", padx=14, pady=(14, 6))
        for rotulo, icone, caminho in locais_rapidos():
            ctk.CTkButton(barra, text=f"  {rotulo}", image=get_icon(icone, 16, c["icon"]),
                          anchor="w", height=32, corner_radius=8, fg_color="transparent",
                          hover_color=c["surface_hover"], text_color=c["text"],
                          font=FONTS["body_small"],
                          command=lambda p=caminho: self._navegar(p)).pack(
                fill="x", padx=8, pady=1)

    def _conteudo(self, parent):
        c = get_colors()
        dir_area = ctk.CTkFrame(parent, fg_color="transparent")
        dir_area.pack(side="left", fill="both", expand=True)

        barra = ctk.CTkFrame(dir_area, fg_color="transparent")
        barra.pack(fill="x")
        ctk.CTkButton(barra, text="", image=get_icon("arrow-up", 16, c["text_muted"]),
                      width=34, height=32, corner_radius=8, fg_color=c["surface_elevated"],
                      hover_color=c["surface_hover"], border_width=1, border_color=c["border"],
                      command=self._subir).pack(side="left", padx=(0, 8))
        self.ent_caminho = ctk.CTkEntry(barra, height=32, font=FONTS["body_small"],
                                        border_color=c["border"])
        self.ent_caminho.pack(side="left", fill="x", expand=True)
        self.ent_caminho.bind("<Return>", lambda _e: self._ir_digitado())
        ctk.CTkButton(barra, text="Ir", width=52, height=32, corner_radius=8,
                      fg_color=c["surface_elevated"], hover_color=c["surface_hover"],
                      text_color=c["text"], border_width=1, border_color=c["border"],
                      command=self._ir_digitado).pack(side="left", padx=(6, 10))

        if self._filetypes:
            rotulos = _rotulos(self._filetypes)
            self.combo_filtro = ctk.CTkOptionMenu(
                barra, values=rotulos, width=190, height=32, font=FONTS["caption"],
                fg_color=c["surface_elevated"], button_color=c["primary"],
                button_hover_color=c["primary_hover"], text_color=c["text"],
                dropdown_fg_color=c["surface_elevated"], dropdown_text_color=c["text"],
                command=self._trocar_filtro)
            self.combo_filtro.set(self._rotulo_filtro)
            self.combo_filtro.pack(side="left")

        lista_card = ctk.CTkFrame(dir_area, fg_color=c["surface_elevated"], corner_radius=14,
                                  border_width=1, border_color=c["border"])
        lista_card.pack(fill="both", expand=True, pady=(8, 8))
        self.lista = scroll_frame(lista_card, fg_color="transparent")
        self.lista.pack(fill="both", expand=True, padx=6, pady=6)
        self.lbl_vazio = ctk.CTkLabel(self.lista, text="Pasta vazia", font=FONTS["body_small"],
                                      text_color=c["text_faint"])

        self._rodape(dir_area)

    def _rodape(self, parent):
        c = get_colors()
        if self._modo == "salvar":
            linha_nome = ctk.CTkFrame(parent, fg_color="transparent")
            linha_nome.pack(fill="x", pady=(0, 6))
            ctk.CTkLabel(linha_nome, text="Nome", font=FONTS["caption"],
                         text_color=c["text_muted"], width=44, anchor="w").pack(side="left")
            self.ent_nome = ctk.CTkEntry(linha_nome, height=32, font=FONTS["body_small"],
                                         border_color=c["border"])
            self.ent_nome.insert(0, self._nome_inicial)
            self.ent_nome.pack(side="left", fill="x", expand=True)
            self.ent_nome.bind("<Return>", lambda _e: self._confirmar())

        rodape = ctk.CTkFrame(parent, fg_color="transparent")
        rodape.pack(fill="x")
        self.chk_ocultos = ctk.CTkCheckBox(rodape, text="Mostrar ocultos",
                                           font=FONTS["caption"], text_color=c["text_muted"],
                                           checkbox_width=18, checkbox_height=18,
                                           command=self._render)
        self.chk_ocultos.pack(side="left")
        self.lbl_status = ctk.CTkLabel(rodape, text="", font=FONTS["caption"],
                                       text_color=c["text_muted"])
        self.lbl_status.pack(side="left", padx=12)
        rotulo = {"pasta": "Selecionar pasta", "salvar": "Salvar"}.get(self._modo, "Abrir")
        if self._multiplo:
            rotulo = "Adicionar"
        ctk.CTkButton(rodape, text=rotulo, width=120, height=36, corner_radius=10,
                      fg_color=c["primary"], hover_color=c["primary_hover"],
                      text_color=c["text_on_primary"], font=FONTS["h3"],
                      command=self._confirmar).pack(side="right")
        ctk.CTkButton(rodape, text="Cancelar", width=96, height=36, corner_radius=10,
                      fg_color="transparent", border_width=1, border_color=c["border"],
                      text_color=c["text_muted"], hover_color=c["surface_hover"],
                      command=self._cancelar).pack(side="right", padx=8)

    # --- navegação ---
    def _diretorio_inicial(self, inicial):
        if inicial and os.path.isdir(inicial):
            return os.path.abspath(inicial)
        if inicial and os.path.isfile(inicial):
            return os.path.dirname(os.path.abspath(inicial))
        casa = os.path.expanduser("~")
        if os.path.isdir(casa):
            return casa
        return os.path.abspath(os.sep)

    def _navegar(self, caminho):
        caminho = os.path.abspath(os.path.expanduser(caminho or self.diretorio))
        if not os.path.isdir(caminho):
            self.lbl_sub.configure(text="Pasta não encontrada", text_color=get_colors()["danger"])
            return
        self.diretorio = caminho
        self._selecionados.clear()
        self.ent_caminho.delete(0, "end")
        self.ent_caminho.insert(0, caminho)
        self.lbl_sub.configure(text=caminho, text_color=get_colors()["text_muted"])
        self._render()

    def _subir(self):
        pai = os.path.dirname(self.diretorio.rstrip(os.sep)) or os.sep
        self._navegar(pai)

    def _ir_digitado(self):
        self._navegar(self.ent_caminho.get().strip())

    def _trocar_filtro(self, rotulo):
        self._rotulo_filtro = rotulo
        self._render()

    def _sufixos_ativos(self):
        if not self._filetypes:
            return ()
        return _sufixos_do_rotulo(self._filetypes, self._rotulo_filtro)

    # --- lista ---
    def _render(self):
        c = get_colors()
        for w in self.lista.winfo_children():
            w.destroy()
        self._linhas.clear()
        self._entradas = listar(self.diretorio,
                                sufixos=self._sufixos_ativos(),
                                incluir_ocultos=bool(self.chk_ocultos.get()),
                                somente_diretorios=self._modo == "pasta")
        if not self._entradas:
            self.lbl_vazio = ctk.CTkLabel(self.lista, text="Nenhum item compatível",
                                          font=FONTS["body_small"], text_color=c["text_faint"])
            self.lbl_vazio.pack(pady=24)
            self._atualizar_status()
            return
        for entrada in self._entradas:
            self._linha(entrada)

    def _linha(self, entrada: Entrada):
        c = get_colors()
        linha = ctk.CTkFrame(self.lista, fg_color="transparent", corner_radius=8, height=34)
        linha.pack(fill="x", pady=1, padx=2)
        if entrada.eh_dir:
            icone, cor = "folder", c["warning"]
        elif entrada.nome.lower().endswith((".xlsx", ".xlsm", ".csv", ".tsv")):
            icone, cor = "sheet", c["success_hover"]
        elif entrada.nome.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".tiff", ".heic")):
            icone, cor = "image", c["accent"]
        else:
            icone, cor = "file", c["text_muted"]
        ctk.CTkLabel(linha, text="", image=get_icon(icone, 18, cor), width=26).pack(
            side="left", padx=(8, 4), pady=6)
        nome_lbl = ctk.CTkLabel(linha, text=entrada.nome, font=FONTS["body_small"], anchor="w",
                                text_color=c["text"])
        nome_lbl.pack(side="left", fill="x", expand=True)
        detalhe = formatar_data(entrada.modificado) if not entrada.eh_dir else ""
        if not entrada.eh_dir:
            detalhe = f"{formatar_tamanho(entrada.tamanho)}   {detalhe}".strip()
        detalhe_lbl = None
        if detalhe:
            detalhe_lbl = ctk.CTkLabel(linha, text=detalhe, font=FONTS["caption"],
                                       text_color=c["text_faint"])
            detalhe_lbl.pack(side="right", padx=10)
        caixa = None
        if self._multiplo and not entrada.eh_dir:
            caixa = ctk.CTkCheckBox(linha, text="", width=20, checkbox_width=18,
                                    checkbox_height=18,
                                    command=lambda e=entrada: self._alternar(e))
            caixa.pack(side="right")

        self._linhas[entrada.caminho] = linha
        alvos = [w for w in (linha, linha.winfo_children()[0], nome_lbl, detalhe_lbl) if w]
        for widget in alvos:
            widget.bind("<Button-1>", lambda _e, e=entrada: self._clique(e), add="+")
            widget.bind("<Double-Button-1>", lambda _e, e=entrada: self._abrir(e), add="+")
            widget.bind("<Enter>", lambda _e, alvo=linha: alvo.configure(fg_color=c["surface_hover"]), add="+")
            widget.bind("<Leave>", lambda _e, alvo=linha, cam=entrada.caminho: self._pintar(alvo, cam), add="+")

    def _pintar(self, linha, caminho):
        c = get_colors()
        if caminho and caminho in self._selecionados:
            linha.configure(fg_color=c["primary_soft"])
        else:
            linha.configure(fg_color="transparent")

    def _clique(self, entrada):
        if entrada.eh_dir:
            return
        if self._multiplo:
            self._alternar(entrada)
            return
        self._selecionados = [entrada.caminho]
        for caminho, linha in self._linhas.items():
            self._pintar(linha, caminho)
        self._atualizar_status()

    def _alternar(self, entrada):
        if entrada.caminho in self._selecionados:
            self._selecionados.remove(entrada.caminho)
        else:
            self._selecionados.append(entrada.caminho)
        self._pintar(self._linhas[entrada.caminho], entrada.caminho)
        self._atualizar_status()

    def _abrir(self, entrada):
        if entrada.eh_dir:
            self._navegar(entrada.caminho)
            return
        if self._modo == "abrir":
            self._selecionados = [entrada.caminho]
            self._confirmar()

    def _atualizar_status(self):
        n = len(self._selecionados)
        if not n:
            self.lbl_status.configure(text="")
        elif n == 1:
            self.lbl_status.configure(text=os.path.basename(self._selecionados[0]))
        else:
            self.lbl_status.configure(text=f"{n} selecionados")

    # --- confirmação ---
    def _confirmar(self):
        foco = self.focus_get()
        if foco in (self.ent_caminho, getattr(self, "ent_nome", None)):
            return
        if self._modo == "pasta":
            self.resultado = self.diretorio
            self.destroy()
            return
        if self._modo == "salvar":
            nome = self.ent_nome.get().strip()
            if not nome:
                self.lbl_status.configure(text="Informe o nome do arquivo",
                                          text_color=get_colors()["danger"])
                return
            if self._defaultextension and not os.path.splitext(nome)[1]:
                nome += self._defaultextension
            self.resultado = os.path.join(self.diretorio, nome)
            self.destroy()
            return
        if self._multiplo:
            if self._selecionados:
                self.resultado = list(self._selecionados)
                self.destroy()
            return
        if self._selecionados:
            self.resultado = self._selecionados[0]
            self.destroy()

    def _cancelar(self):
        self.resultado = None
        self.destroy()

    def _centralizar(self):
        try:
            self.update_idletasks()
            pai = self.master.winfo_toplevel()
            x = pai.winfo_rootx() + max(0, (pai.winfo_width() - self.winfo_width()) // 2)
            y = pai.winfo_rooty() + max(0, (pai.winfo_height() - self.winfo_height()) // 2)
            self.geometry(f"+{x}+{y}")
        except Exception:
            pass


def _raiz(parent):
    if hasattr(parent, "winfo_toplevel"):
        return parent.winfo_toplevel()
    return getattr(parent, "root", parent)


def _executar(parent, **kwargs):
    janela = SeletorArquivos(parent, **kwargs)
    parent.wait_window(janela)
    return janela.resultado


def escolher_arquivo(parent, *, titulo="Escolher arquivo", filetypes=None, inicial=None):
    return _executar(parent, titulo=titulo, filetypes=filetypes, inicial=inicial)


def escolher_arquivos(parent, *, titulo="Escolher arquivos", filetypes=None, inicial=None):
    return _executar(parent, titulo=titulo, filetypes=filetypes, inicial=inicial,
                     multiplo=True) or []


def escolher_pasta(parent, *, titulo="Escolher pasta", inicial=None):
    return _executar(parent, titulo=titulo, inicial=inicial, modo="pasta")


def salvar_arquivo(parent, *, titulo="Salvar arquivo", filetypes=None, inicial=None,
                   nome_inicial="", defaultextension=""):
    return _executar(parent, titulo=titulo, filetypes=filetypes, inicial=inicial,
                     modo="salvar", nome_inicial=nome_inicial,
                     defaultextension=defaultextension)
