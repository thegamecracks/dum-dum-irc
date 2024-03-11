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

        self.apply_last_connect_entries()

        self._connect_bind = app.bind("<Return>", lambda event: self.do_connect())

        self._connection_attempt = None
        self._destroying = False

    def apply_last_connect_entries(self) -> None:
        with self.app.store_factory() as store:
            host = store.get_setting("last-connect-host", "127.0.0.1")
            port = store.get_setting("last-connect-port", 6667)
            nick = store.get_setting("last-connect-nick", "Somebody")

        self.host_entry_var.set(host)
        self.port_entry_var.set(port)
        self.nick_entry_var.set(nick)

    def do_connect(self) -> None:
        fut = self._connection_attempt
        if fut is not None and not fut.done():
            return

        host = self.host_entry_var.get()
        port = int(self.port_entry_var.get())
        nick = self.nick_entry_var.get()

        self.set_last_connect_entries(host, port, nick)

        coro = self.app.attempt_connection(host, port, nick)
        self._connection_attempt = self.app.submit(coro)

        self.connect.state(["disabled"])
        self._connection_attempt.add_done_callback(self._on_connection_attempt)

    def set_last_connect_entries(self, host: str, port: int, nick: str) -> None:
        with self.app.store_factory() as store:
            store.set_setting("last-connect-host", host)
            store.set_setting("last-connect-port", port)
            store.set_setting("last-connect-nick", nick)

    def destroy(self) -> None:
        self._destroying = True
        self.app.unbind("<Return>", self._connect_bind)
        super().destroy()

    def _on_connection_attempt(self, fut: concurrent.futures.Future) -> None:
        if self._destroying:
            return

        self.connect.state(["!disabled"])
