from tkinter import Canvas, Event, Widget
from tkinter.ttk import Frame, Scrollbar, Style
from weakref import WeakSet


class ScrollableFrame(Frame):
    _last_scrollregion: tuple[int, int, int, int] | None

    def __init__(
        self,
        *args,
        autoscroll: bool = False,
        xscroll: bool = False,
        yscroll: bool = False,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        self.autoscroll = autoscroll
        self.xscroll = xscroll
        self.yscroll = yscroll

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

        self._last_scrollregion = None
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
        scroll_edges = self._get_scroll_edges()

        # self._canvas.bbox("all") doesn't update until window resize
        # so we're relying on the inner frame's requested height instead.
        new_width = self._canvas.winfo_width()
        new_height = self._canvas.winfo_height()
        if self.xscroll:
            new_width = max(new_width, self.inner.winfo_reqwidth())
        if self.yscroll:
            new_height = max(new_height, self.inner.winfo_reqheight())

        bbox = (0, 0, new_width, new_height)
        self._canvas.configure(scrollregion=bbox)
        self._canvas.itemconfigure(self._inner_id, width=new_width, height=new_height)

        self._update_scrollbar_visibility(self._xscrollbar)
        self._update_scrollbar_visibility(self._yscrollbar)
        self._propagate_scroll_binds(self.inner)
        self._update_scroll_edges(bbox, *scroll_edges)

    def _get_scroll_edges(self) -> tuple[bool, bool]:
        xview = self._canvas.xview()
        yview = self._canvas.yview()
        scrolled_to_right = xview[1] == 1 and xview[0] != 0
        scrolled_to_bottom = yview[1] == 1 and yview[0] != 0
        return scrolled_to_right, scrolled_to_bottom

    def _propagate_scroll_binds(self, parent: Widget):
        if parent not in self._scrolled_widgets:
            parent.bind("<MouseWheel>", self._on_mouse_yscroll)
            parent.bind("<Shift-MouseWheel>", self._on_mouse_xscroll)
            self._scrolled_widgets.add(parent)

        for child in parent.winfo_children():
            self._propagate_scroll_binds(child)

    def _update_scroll_edges(
        self,
        bbox: tuple[int, int, int, int],
        scrolled_to_right: bool,
        scrolled_to_bottom: bool,
    ) -> None:
        self._last_scrollregion, last_bbox = bbox, self._last_scrollregion
        if not self.autoscroll:
            return
        elif bbox == last_bbox:
            return

        if scrolled_to_right:
            self._canvas.xview_moveto(1)
        if scrolled_to_bottom:
            self._canvas.yview_moveto(1)

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
