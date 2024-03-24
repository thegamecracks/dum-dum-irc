from pathlib import Path
from tkinter import StringVar, filedialog
from tkinter.ttk import Button, Entry, Frame, Label
from typing import Any

ALL_FILETYPE = ("All files", ("*",))
SSL_CERTIFICATE_FILETYPE = (
    "SSL Certificate",
    ("*.pem", "*.crt", "*.ca-bundle", "*.cer"),
)


class FileEntry(Frame):
    def __init__(
        self,
        parent: Frame,
        *,
        browse_kwargs: dict[str, Any] | None = None,
        text: str = "",
    ) -> None:
        super().__init__(parent)

        if browse_kwargs is None:
            browse_kwargs = {}
        self.browse_kwargs = browse_kwargs

        self.grid_columnconfigure(1, weight=1)

        self._validatecommand = (self.register(self._validate), "%P")

        self.label = Label(self, text=text)
        self.label.grid(row=0, column=0)

        self.var = StringVar(self)
        self.entry = Entry(
            self,
            textvariable=self.var,
            validate="focusout",
            validatecommand=self._validatecommand,
        )
        self.entry.grid(row=0, column=1, sticky="ew")

        self.browse = Button(self, text="Browse", command=self.do_browse)
        self.browse.grid(row=0, column=2)

    def enable(self, enabled: bool) -> None:
        state = ["!disabled" if enabled else "disabled"]
        self.entry.state(state)
        self.browse.state(state)

    def get(self) -> str:
        return self.var.get().strip()

    def get_path(self) -> Path | None:
        filename = self.get()
        if filename != "":
            return Path(filename)

    def do_browse(self) -> None:
        filename = filedialog.askopenfilename(**self.browse_kwargs)
        if filename != "":
            self.var.set(filename)

    def _validate(self, val: str) -> bool:
        return Path(val).is_file()
