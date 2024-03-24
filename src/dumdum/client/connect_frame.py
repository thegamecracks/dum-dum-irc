import concurrent.futures
import logging
import ssl
from pathlib import Path
from tkinter import BooleanVar, StringVar, messagebox
from tkinter.ttk import Button, Checkbutton, Entry, Frame, Label

from .app import TkApp
from .file_entry import SSL_CERTIFICATE_FILETYPES, FileEntry

log = logging.getLogger(__name__)


class ConnectFrame(Frame):
    _connection_attempt: concurrent.futures.Future[None] | None

    def __init__(self, app: TkApp):
        super().__init__(padding=10)

        self.app = app

        self.grid_columnconfigure(1, weight=1)

        self.host_label = Label(self, text="Host:")
        self.host_label.grid(row=0, column=0, sticky="w")
        self.host_entry_var = StringVar(self)
        self.host_entry = Entry(self, textvariable=self.host_entry_var)
        self.host_entry.grid(row=0, column=1, sticky="ew")

        self.port_label = Label(self, text="Port:")
        self.port_label.grid(row=1, column=0, sticky="w")
        self.port_entry_var = StringVar(self)
        self.port_entry = Entry(self, textvariable=self.port_entry_var)
        self.port_entry.grid(row=1, column=1, sticky="ew")

        self.ssl_enabled_var = BooleanVar(self, value=False)
        self.ssl_enabled = Checkbutton(
            self,
            text="Use SSL?",
            variable=self.ssl_enabled_var,
        )
        self.ssl_enabled.grid(row=2, column=0, sticky="w")
        self.ssl_enabled_var.trace_add("write", self._on_cert_check_var_write)

        self.ssl_cert = FileEntry(
            self,
            text="Certificate (Optional):",
            browse_kwargs={
                "title": "Use Certificate File",
                "filetypes": SSL_CERTIFICATE_FILETYPES,
            },
        )
        self.ssl_cert.grid(row=2, column=1, padx=(15, 0), sticky="ew")

        self.nick_label = Label(self, text="Nickname:")
        self.nick_label.grid(row=3, column=0, sticky="w")
        self.nick_entry_var = StringVar(self)
        self.nick_entry = Entry(self, textvariable=self.nick_entry_var)
        self.nick_entry.grid(row=3, column=1, sticky="ew")

        self.connect = Button(self, text="Connect", command=self.do_connect)
        self.connect.grid(row=3, column=1, sticky="e")

        self.apply_last_connect_entries()

        self._connect_bind = app.bind("<Return>", lambda event: self.do_connect())

        self._connection_attempt = None
        self._destroying = False

    def apply_last_connect_entries(self) -> None:
        with self.app.store_factory() as store:
            host = store.get_setting("last-connect-host", "127.0.0.1")
            port = store.get_setting("last-connect-port", 6667)
            nick = store.get_setting("last-connect-nick", "Somebody")
            ssl_enabled = store.get_setting("last-connect-ssl-enabled", False)
            ssl_cert = store.get_setting("last-connect-ssl-cert", "")

        self.host_entry_var.set(host)
        self.port_entry_var.set(port)
        self.nick_entry_var.set(nick)
        self.ssl_enabled_var.set(ssl_enabled)
        self.ssl_cert.var.set(ssl_cert)

    def do_connect(self) -> None:
        fut = self._connection_attempt
        if fut is not None and not fut.done():
            return

        host = self.host_entry_var.get()
        port = int(self.port_entry_var.get())
        nick = self.nick_entry_var.get()
        ssl_enabled = self.ssl_enabled_var.get()
        ssl_cert = self.ssl_cert.get()

        if ssl_enabled:
            path = self.ssl_cert.get_path()
            if path is not None and not path.is_file():
                messagebox.showerror(
                    "Certificate Not Found",
                    "The SSL certificate path does not exist.",
                )
                return

            try:
                ssl_context = self._create_ssl_context(path)
            except ssl.SSLError as e:
                log.error("Could not create SSL context", exc_info=e)
                messagebox.showerror(
                    "Invalid Certificate",
                    "The SSL certificate could not be loaded.",
                )
                return

        else:
            ssl_context = None

        self.set_last_connect_entries(host, port, nick, ssl_enabled, ssl_cert)

        coro = self.app.attempt_connection(host, port, nick, ssl=ssl_context)
        self._connection_attempt = self.app.submit(coro)

        self.connect.state(["disabled"])
        self._connection_attempt.add_done_callback(self._on_connection_attempt)

    def set_last_connect_entries(
        self,
        host: str,
        port: int,
        nick: str,
        ssl_enabled: bool,
        ssl_cert: str,
    ) -> None:
        with self.app.store_factory() as store:
            store.set_setting("last-connect-host", host)
            store.set_setting("last-connect-port", port)
            store.set_setting("last-connect-nick", nick)
            store.set_setting("last-connect-ssl-enabled", ssl_enabled)
            store.set_setting("last-connect-ssl-cert", ssl_cert)

    def destroy(self) -> None:
        self._destroying = True
        self.app.unbind("<Return>", self._connect_bind)
        super().destroy()

    def _on_cert_check_var_write(self, *args) -> None:
        enabled = self.ssl_enabled_var.get()
        self.ssl_cert.enable(enabled)

    def _create_ssl_context(self, cafile: str | Path | None) -> ssl.SSLContext:
        if cafile is not None:
            cafile = str(cafile)

        context = ssl.create_default_context(cafile=cafile)

        # WARNING: for ease of server setup, skip hostname checks for self-signed certs
        if cafile is not None:
            context.check_hostname = False

        return context

    def _on_connection_attempt(self, fut: concurrent.futures.Future) -> None:
        if self._destroying:
            return

        self.connect.state(["!disabled"])
