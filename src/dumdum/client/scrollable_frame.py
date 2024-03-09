from tkinter import Canvas, Event, Widget
from tkinter.ttk import Frame, Scrollbar, Style
from weakref import WeakSet


class ScrollableFrame(Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._canvas = Canvas(self, highlightthickness=0)
        self._canvas.grid(row=0, column=0, sticky="nesw")

        self._xscrollbar = Scrollbar(self, orient="horizontal")
        self._yscrollbar = Scrollbar(self, orient="vertical")

        # Use rowspan=2 or columnspan=2 appropriately if filling the
        # bottom-right corner of the frame is desired.
        self._xscrollbar.grid(row=1, column=0, sticky="ew")
        self._yscrollbar.grid(row=0, column=1, sticky="ns")

        self._xscrollbar["command"] = self._canvas.xview
        self._yscrollbar["command"] = self._canvas.yview
        self._canvas["xscrollcommand"] = self._wrap_scrollbar_set(self._xscrollbar)
        self._canvas["yscrollcommand"] = self._wrap_scrollbar_set(self._yscrollbar)

        self.inner = Frame(self._canvas)
        self._inner_id = self._canvas.create_window(
            (0, 0), window=self.inner, anchor="nw"
        )

        self._canvas.bind("<Configure>", lambda event: self._update())
        self.inner.bind("<Configure>", self._on_inner_configure)

        self._scrolled_widgets = WeakSet()
        self._style = Style(self)
        self._update_rate = 125
        self._update_loop()

    def _on_inner_configure(self, event: Event):
        background = self._style.lookup(self.inner.winfo_class(), "background")
        self._canvas.configure(background=background)
        self._update()

    def _update_loop(self):
        # Without this, any changes to the inner frame won't affect
        # the scroll bar/region until the window is resized.
        self._update()
        self.after(self._update_rate, self._update_loop)

    def _update(self):
        # self._canvas.bbox("all") doesn't update until window resize
        # so we're relying on the inner frame's requested height instead.
        new_width = max(self._canvas.winfo_width(), self.inner.winfo_reqwidth())
        new_height = max(self._canvas.winfo_height(), self.inner.winfo_reqheight())
        bbox = (0, 0, new_width, new_height)
        self._canvas.configure(scrollregion=bbox)
        self._canvas.itemconfigure(self._inner_id, width=new_width, height=new_height)

        self._update_scrollbar_visibility(self._xscrollbar)
        self._update_scrollbar_visibility(self._yscrollbar)
        self._propagate_scroll_binds(self.inner)

    def _propagate_scroll_binds(self, parent: Widget):
        if parent not in self._scrolled_widgets:
            parent.bind("<MouseWheel>", self._on_mouse_yscroll)
            parent.bind("<Shift-MouseWheel>", self._on_mouse_xscroll)
            self._scrolled_widgets.add(parent)

        for child in parent.winfo_children():
            self._propagate_scroll_binds(child)

    def _on_mouse_xscroll(self, event: Event):
        delta = int(-event.delta / 100)
        self._canvas.xview_scroll(delta, "units")

    def _on_mouse_yscroll(self, event: Event):
        delta = int(-event.delta / 100)
        self._canvas.yview_scroll(delta, "units")

    def _update_scrollbar_visibility(self, scrollbar: Scrollbar):
        if scrollbar.get() == (0, 1):
            scrollbar.grid_remove()
        else:
            scrollbar.grid()

    def _wrap_scrollbar_set(self, scrollbar: Scrollbar):
        def wrapper(*args, **kwargs):
            scrollbar.set(*args, **kwargs)
            self._update_scrollbar_visibility(scrollbar)

        return wrapper
