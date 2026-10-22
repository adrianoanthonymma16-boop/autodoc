"""
Avisos e confirmações no tema do app (substitui tkinter.messagebox).

API compatível com o messagebox do Tk:
    showinfo(title, message) / showwarning(...) / showerror(...)
    askyesno(title, message) -> bool
    askokcancel(title, message) -> bool
e ainda pedir_texto(...) no lugar de simpledialog.askstring.
"""
from __future__ import annotations

import tkinter
from dataclasses import dataclass

import customtkinter as ctk

from ui.icons import get as get_icon
from ui.theme import FONTS, get_colors


@dataclass(frozen=True)
class _Estilo:
    icone: str
    cor: str
    cor_soft: str
    padrao: str


def _estilo(tipo: str) -> _Estilo:
    c = get_colors()
    if tipo == "erro":
        return _Estilo("alert", c["danger"], c["danger_soft"], "Entendi")
    if tipo == "aviso":
        return _Estilo("alert", c["warning"], c["warning_soft"], "Entendi")
    if tipo == "pergunta":
        return _Estilo("info", c["primary"], c["primary_soft"], "Sim")
    return _Estilo("check", c["success"], c["success_soft"], "OK")


def _raiz(parent=None):
    if parent is not None:
        if hasattr(parent, "winfo_toplevel"):
            return parent.winfo_toplevel()
        if hasattr(parent, "root"):
            return parent.root
    return tkinter._default_root


def _centralizar(janela, raiz):
    try:
        janela.update_idletasks()
        x = raiz.winfo_rootx() + max(0, (raiz.winfo_width() - janela.winfo_width()) // 2)
        y = raiz.winfo_rooty() + max(0, (raiz.winfo_height() - janela.winfo_height()) // 2)
        janela.geometry(f"+{x}+{y}")
    except Exception:
        pass


class _Dialogo(ctk.CTkToplevel):
    def __init__(self, raiz, titulo, mensagem, tipo):
        super().__init__(raiz)
        c = get_colors()
        self.resultado = None
        self._estilo = _estilo(tipo)
        self.title(titulo or "AutoDoc")
        self.configure(fg_color=c["bg"])
        self.resizable(False, False)
        largura = 470
        linhas = sum(max(1, len(linha) // 56 + 1) for linha in (mensagem or "").splitlines())
        altura = max(190, 150 + linhas * 19)
        self.geometry(f"{largura}x{min(altura, 560)}")
        self.transient(raiz)
        self.protocol("WM_DELETE_WINDOW", self._cancelar)
        self.bind("<Escape>", lambda _e: self._cancelar())
        self.bind("<Return>", lambda _e: self._confirmar())

        corpo = ctk.CTkFrame(self, fg_color="transparent")
        corpo.pack(fill="both", expand=True, padx=24, pady=(22, 16))
        topo = ctk.CTkFrame(corpo, fg_color="transparent")
        topo.pack(fill="x")
        selo = ctk.CTkFrame(topo, fg_color=self._estilo.cor_soft, corner_radius=14,
                            width=46, height=46)
        selo.pack(side="left", padx=(0, 14))
        selo.pack_propagate(False)
        ctk.CTkLabel(selo, text="", image=get_icon(self._estilo.icone, 22, self._estilo.cor),
                     width=46, height=46).pack(expand=True)
        textos = ctk.CTkFrame(topo, fg_color="transparent")
        textos.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(textos, text=titulo or "AutoDoc", font=FONTS["h1"],
                     text_color=c["text"], anchor="w", justify="left").pack(anchor="w")
        self.lbl_msg = ctk.CTkLabel(corpo, text=mensagem or "", font=FONTS["body"],
                                    text_color=c["text_muted"], wraplength=largura - 60,
                                    justify="left", anchor="w")
        self.lbl_msg.pack(fill="x", pady=(16, 10))

        self.acoes = ctk.CTkFrame(corpo, fg_color="transparent")
        self.acoes.pack(fill="x", side="bottom")
        self.after(60, lambda: _centralizar(self, raiz))

    def _botao(self, texto, primario, comando):
        c = get_colors()
        if primario:
            return ctk.CTkButton(self.acoes, text=texto, height=38, width=112, corner_radius=10,
                                 fg_color=self._estilo.cor, hover_color=self._estilo.cor,
                                 text_color=c["text_on_primary"], font=FONTS["h3"],
                                 command=comando)
        return ctk.CTkButton(self.acoes, text=texto, height=38, width=104, corner_radius=10,
                             fg_color="transparent", border_width=1, border_color=c["border"],
                             text_color=c["text_muted"], hover_color=c["surface_hover"],
                             command=comando)

    def _confirmar(self):
        self.resultado = True
        self.destroy()

    def _cancelar(self):
        self.resultado = False
        self.destroy()


def _mostrar(tipo, titulo, mensagem, parent=None):
    raiz = _raiz(parent)
    if raiz is None:
        return None
    janela = _Dialogo(raiz, titulo, mensagem, tipo)
    if tipo == "pergunta":
        janela._botao("Não", False, janela._cancelar).pack(side="right", padx=(8, 0))
        janela._botao("Sim", True, janela._confirmar).pack(side="right")
    else:
        janela._botao(_estilo(tipo).padrao, True, janela._confirmar).pack(side="right")
    janela.wait_visibility()
    janela.grab_set()
    janela.focus_force()
    raiz.wait_window(janela)
    return janela.resultado


def showinfo(title=None, message=None, parent=None, **_):
    _mostrar("info", title, message, parent)
    return "ok"


def showwarning(title=None, message=None, parent=None, **_):
    _mostrar("aviso", title, message, parent)
    return "ok"


def showerror(title=None, message=None, parent=None, **_):
    _mostrar("erro", title, message, parent)
    return "ok"


def askyesno(title=None, message=None, parent=None, **_):
    resultado = _mostrar("pergunta", title, message, parent)
    return bool(resultado)


def askokcancel(title=None, message=None, parent=None, **_):
    return bool(_mostrar("pergunta", title, message, parent))


class _DialogoTexto(_Dialogo):
    def __init__(self, raiz, titulo, mensagem, inicial=""):
        super().__init__(raiz, titulo, mensagem, "pergunta")
        self.geometry("470x300")
        c = get_colors()
        self.entrada = ctk.CTkEntry(self.lbl_msg.master, height=36, font=FONTS["body"],
                                    border_color=c["border"])
        self.entrada.insert(0, inicial)
        self.entrada.pack(fill="x", pady=(0, 12))
        self._botao("Salvar", True, self._confirmar).pack(side="right")
        self._botao("Cancelar", False, self._cancelar).pack(side="right", padx=(0, 8))
        self.bind("<Return>", lambda _e: self._confirmar())
        self.after(80, self.entrada.focus_set)

    def _confirmar(self):
        self.resultado = self.entrada.get().strip() or None
        self.destroy()


def pedir_texto(title=None, message=None, parent=None, inicial="", **_):
    raiz = _raiz(parent)
    if raiz is None:
        return None
    janela = _DialogoTexto(raiz, title, message, inicial)
    janela.wait_visibility()
    janela.grab_set()
    raiz.wait_window(janela)
    return janela.resultado
