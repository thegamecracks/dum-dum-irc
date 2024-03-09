import concurrent.futures
from tkinter import StringVar
from tkinter.ttk import Button, Entry, Frame, Label

from .app import TkApp


class ConnectFrame(Frame):
    _connection_attempt: concurrent.futures.Future[None] | None

    def __init__(self, app: TkApp):
        super().__init__(padding=10)

        self.app = app

        self.grid_columnconfigure(1, weight=1)

        self.host_label = Label(self, text="Host:")
        self.host_label.grid(row=0, column=0)
        self.host_entry_var = StringVar(self)
        self.host_entry = Entry(self, textvariable=self.host_entry_var)
        self.host_entry.grid(row=0, column=1, sticky="ew")

        self.port_label = Label(self, text="Port:")
        self.port_label.grid(row=1, column=0)
        self.port_entry_var = StringVar(self)
        self.port_entry = Entry(self, textvariable=self.port_entry_var)
        self.port_entry.grid(row=1, column=1, sticky="ew")

        self.nick_label = Label(self, text="Nickname:")
        self.nick_label.grid(row=2, column=0)
        self.nick_entry_var = StringVar(self)
        self.nick_entry = Entry(self, textvariable=self.nick_entry_var)
        self.nick_entry.grid(row=2, column=1, sticky="ew")

        self.connect = Button(self, text="Connect", command=self.do_connect)
        self.connect.grid(row=2, column=1, sticky="e")

        # TODO: replace hardcoded defaults with user data
        self.host_entry_var.set("127.0.0.1")
        self.port_entry_var.set("6667")
        self.nick_entry_var.set("Somebody")

        self._connect_bind = app.bind("<Return>", lambda event: self.do_connect())

        self._connection_attempt = None

    def do_connect(self) -> None:
        fut = self._connection_attempt
        if fut is not None and not fut.done():
            return

        host = self.host_entry_var.get()
        port = int(self.port_entry_var.get())
        nick = self.nick_entry_var.get()

        coro = self.app.attempt_connection(host, port, nick)
        self._connection_attempt = self.app.submit(coro)

        self.connect.state(["disabled"])
        self._connection_attempt.add_done_callback(
            lambda fut: self.connect.state(["!disabled"])
        )

    def destroy(self) -> None:
        self.app.unbind("<Return>", self._connect_bind)
        super().destroy()
