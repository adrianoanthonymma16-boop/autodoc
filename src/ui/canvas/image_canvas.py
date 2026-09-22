"""
ImageCanvas - corrige bugs de pan/zoom e coords, cross-platform
"""
import contextlib
import tkinter as tk

import customtkinter as ctk
from customtkinter.windows.widgets.scaling.scaling_tracker import ScalingTracker
from PIL import Image, ImageTk

from ui.theme import get_colors


class ImageCanvas(ctk.CTkFrame):
    def __init__(self, parent, on_rect_done=None, **kwargs):
        super().__init__(parent, **kwargs)
        c = get_colors()
        self.on_rect_done = on_rect_done
        self.imagem_original = None
        self.imagem_tk = None
        self.imagem_resized = None
        self.zoom = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self._is_panning = False
        self._pan_start = (0,0)
        self._rect_id = None
        self._start = None
        self._overlays = []

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(self, bg=c["canvas_bg"], highlightthickness=0, bd=0)
        self.canvas.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        self.scroll_y = ctk.CTkScrollbar(self, orientation="vertical", command=self.canvas.yview)
        self.scroll_y.grid(row=0, column=1, sticky="ns", padx=(0,2), pady=2)
        self.canvas.configure(yscrollcommand=self.scroll_y.set)

        # toolbar inferior
        self.toolbar = ctk.CTkFrame(self, fg_color="transparent")
        self.toolbar.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(6,0))
        self.lbl_zoom = ctk.CTkLabel(self.toolbar, text="100%", font=("Inter", 10), text_color=c["text_muted"])
        self.lbl_zoom.pack(side="right", padx=6)
        ctk.CTkButton(self.toolbar, text="－", width=28, height=24, corner_radius=8, command=lambda: self.zoom_by(0.8), fg_color=c["surface"], text_color=c["text"], border_width=1, border_color=c["border"]).pack(side="right", padx=2)
        ctk.CTkButton(self.toolbar, text="＋", width=28, height=24, corner_radius=8, command=lambda: self.zoom_by(1.25), fg_color=c["surface"], text_color=c["text"], border_width=1, border_color=c["border"]).pack(side="right", padx=2)
        ctk.CTkButton(self.toolbar, text="100%", width=44, height=24, corner_radius=8, command=self.reset_view, fg_color=c["surface"], text_color=c["text"], border_width=1, border_color=c["border"]).pack(side="right", padx=2)

        self._bind_events()

    def _bind_events(self):
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        # pan: botão do meio ou Shift+drag
        self.canvas.bind("<ButtonPress-2>", self._pan_start_ev)
        self.canvas.bind("<B2-Motion>", self._pan_move_ev)
        self.canvas.bind("<ButtonRelease-2>", self._pan_end_ev)
        self.canvas.bind("<Shift-ButtonPress-1>", self._pan_start_ev)
        self.canvas.bind("<Shift-B1-Motion>", self._pan_move_ev)
        self.canvas.bind("<Shift-ButtonRelease-1>", self._pan_end_ev)
        # zoom cross-platform
        self.canvas.bind("<Control-MouseWheel>", lambda e: self.zoom_by(1.2 if e.delta>0 else 0.8))
        self.canvas.bind("<Control-Button-4>", lambda e: self.zoom_by(1.2))  # linux
        self.canvas.bind("<Control-Button-5>", lambda e: self.zoom_by(0.8))
        # also without ctrl? keep ctrl only
        self.canvas.bind("<MouseWheel>", self._on_wheel_scroll)  # scroll normal

    def _on_wheel_scroll(self, e):
        # normal scroll
        self.canvas.yview_scroll(int(-1*(e.delta/120)), "units")

    def set_image(self, pil_image):
        self.imagem_original = pil_image
        self.zoom = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self._redraw()

    def _redraw(self):
        if not self.imagem_original:
            self.canvas.delete("all")
            return
        scale = ScalingTracker.get_window_scaling(self) or 1.0
        w = int(self.imagem_original.width * self.zoom * scale)
        h = int(self.imagem_original.height * self.zoom * scale)
        w = max(1, w); h = max(1, h)
        self.imagem_resized = self.imagem_original.resize((w, h), Image.Resampling.LANCZOS)
        self.imagem_tk = ImageTk.PhotoImage(self.imagem_resized)
        self.canvas.delete("all")
        self.canvas.config(scrollregion=(0,0,w,h))
        self.canvas.create_image(self.pan_x, self.pan_y, anchor=tk.NW, image=self.imagem_tk)
        # redesenha overlays capturados externamente via callback
        for fn in self._overlays:
            with contextlib.suppress(Exception):
                fn(self)
        self.lbl_zoom.configure(text=f"{int(self.zoom*100)}%")

    def set_overlays(self, fns):
        self._overlays = fns
        self._redraw()

    def zoom_by(self, factor):
        self.zoom = max(0.15, min(self.zoom*factor, 6.0))
        self._redraw()

    def reset_view(self):
        self.zoom = 1.0; self.pan_x=0; self.pan_y=0; self._redraw()

    # --- pan ---
    def _pan_start_ev(self, e):
        self._is_panning=True
        self._pan_start=(e.x,e.y)
        self.canvas.config(cursor="fleur")
    def _pan_move_ev(self, e):
        if self._is_panning:
            dx=e.x-self._pan_start[0]
            dy=e.y-self._pan_start[1]
            self.pan_x+=dx; self.pan_y+=dy
            self._pan_start=(e.x,e.y)
            self.canvas.move("all", dx, dy)
    def _pan_end_ev(self, e):
        self._is_panning=False
        self.canvas.config(cursor="")

    # --- retângulo ---
    def _on_press(self, e):
        if self._is_panning:
            return
        if not self.imagem_original:
            return
        x=self.canvas.canvasx(e.x)
        y=self.canvas.canvasy(e.y)
        self._start=(x,y)
        c = get_colors()
        self._rect_id=self.canvas.create_rectangle(x,y,x,y, outline=c["primary"], width=2, dash=(6,4))

    def _on_drag(self, e):
        if self._rect_id and self._start:
            x=self.canvas.canvasx(e.x)
            y=self.canvas.canvasy(e.y)
            self.canvas.coords(self._rect_id, self._start[0], self._start[1], x, y)

    def _on_release(self, e):
        if not self._rect_id or not self._start:
            return
        x=self.canvas.canvasx(e.x)
        y=self.canvas.canvasy(e.y)
        x1=min(self._start[0], x); y1=min(self._start[1], y); x2=max(self._start[0], x); y2=max(self._start[1], y)
        if (x2-x1)>12 and (y2-y1)>12:
            # converte de canvas coords (com pan+zoom) para coords da imagem original
            # canvas image está em (pan_x, pan_y) com escala zoom
            escala_x = self.imagem_original.width / self.imagem_resized.width
            escala_y = self.imagem_original.height / self.imagem_resized.height
            rx1=int((x1 - self.pan_x)*escala_x)
            ry1=int((y1 - self.pan_y)*escala_y)
            rx2=int((x2 - self.pan_x)*escala_x)
            ry2=int((y2 - self.pan_y)*escala_y)
            # clamp
            rx1=max(0, min(rx1, self.imagem_original.width))
            ry1=max(0, min(ry1, self.imagem_original.height))
            rx2=max(0, min(rx2, self.imagem_original.width))
            ry2=max(0, min(ry2, self.imagem_original.height))
            self.canvas.itemconfig(self._rect_id, outline=get_colors()["accent"], dash=())
            if self.on_rect_done:
                self.on_rect_done(rx1, ry1, rx2, ry2)
        else:
            self.canvas.delete(self._rect_id)
        self._rect_id=None
        self._start=None

    def draw_rects(self, rects, color=None, label_color=None):
        """rects: list of dict x1,y1,x2,y2 + label"""
        if not self.imagem_original or not self.imagem_resized:
            return
        c = get_colors()
        color = color or c["primary"]
        label_color = label_color or c["primary"]
        sx=self.imagem_resized.width/self.imagem_original.width
        sy=self.imagem_resized.height/self.imagem_original.height
        for r in rects:
            x1=r['x1']*sx+self.pan_x; y1=r['y1']*sy+self.pan_y
            x2=r['x2']*sx+self.pan_x; y2=r['y2']*sy+self.pan_y
            self.canvas.create_rectangle(x1,y1,x2,y2, outline=color, width=2)
            if r.get('label'):
                self.canvas.create_text(x1, max(0,y1-6), text=r['label'], fill=label_color, anchor=tk.SW, font=("Inter", 9, "bold"))
