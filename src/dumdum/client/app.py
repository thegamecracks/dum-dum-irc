import asyncio
import concurrent.futures
import logging
import queue
import ssl
import traceback
from tkinter import Event, Tk, messagebox
from tkinter.ttk import Frame
from typing import Any, Awaitable, ContextManager, Protocol, runtime_checkable

from dumdum.protocol import (
    ClientEvent,
    ClientEventAuthentication,
    ClientEventIncompatibleVersion,
)

from .async_client import AsyncClient
from .errors import AuthenticationFailedError
from .event_thread import EventThread
from .store import ClientStore

log = logging.getLogger(__name__)


def reset_during_ssl_handshake(exc: ConnectionResetError) -> bool:
    for stack in traceback.extract_tb(exc.__traceback__):
        if "handshake" in stack.name:
            return True
        if stack.line is not None and "handshake" in stack.line:
            return True
    return False


class ClientStoreFactory(Protocol):
    def __call__(self) -> ContextManager[ClientStore]: ...


class TkApp(Tk):
    client: AsyncClient  # NOTE: only assigned in attempt_connection()
    _client_events: queue.Queue[ClientEvent]
    _last_connection_exc: BaseException | None

    def __init__(
        self,
        event_thread: EventThread,
        store_factory: ClientStoreFactory,
    ):
        super().__init__()

        self.event_thread = event_thread
        self.store_factory = store_factory

        self._connect_lifetime_with_event_thread(event_thread)

        self._client_events = queue.Queue()
        self._last_connection_exc = None

        self.title("Dumdum Client")
        self.geometry("900x600")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.frame = Frame(self)
        self.frame.grid()

        self.bind("<<Destroy>>", self._on_destroy)
        self.bind("<<ClientEvent>>", self._on_client_event)
        self.bind("<<ConnectionLost>>", self._on_connection_lost)

    def switch_frame(self, frame: Frame) -> None:
        self.frame.destroy()
        self.frame = frame
        self.frame.grid(sticky="nesw")

    def submit(self, coro: Awaitable[Any]) -> concurrent.futures.Future:
        fut = asyncio.run_coroutine_threadsafe(coro, self.event_thread.loop)
        fut.add_done_callback(log_fut_exception)
        return fut

    async def attempt_connection(
        self,
        host: str,
        port: int,
        nick: str,
        *,
        ssl: ssl.SSLContext | None,
    ) -> None:
        self.client = AsyncClient(nick, event_callback=self._handle_event_threadsafe)

        coro = self._run_connection(host, port, ssl=ssl)
        self._connection_task = asyncio.create_task(coro)

        await self.client._wait_for_authentication()

    def _connect_lifetime_with_event_thread(self, event_thread: EventThread) -> None:
        # In our application we'll be running an asyncio event loop in
        # a separate thread. This event loop may try to run methods on
        # our GUI like event_generate(), which requires the GUI to be running.
        # If the GUI is destroyed first, it may cause a deadlock
        # in the other thread, preventing our program from exiting.
        # As such, we need to defer GUI destruction until the event thread
        # is finished.
        event_callback = lambda fut: self.event_generate("<<Destroy>>")
        event_thread.finished_fut.add_done_callback(event_callback)

    def destroy(self) -> None:
        self.event_thread.stop()

    def _on_destroy(self, event: Event) -> None:
        super().destroy()

    async def _run_connection(
        self,
        host: str,
        port: int,
        *,
        ssl: ssl.SSLContext | None,
    ) -> None:
        try:
            async with self.client.connect(host, port, ssl=ssl):
                await self.client.run_forever()
        except BaseException as e:
            self._last_connection_exc = e
        else:
            self._last_connection_exc = None
        finally:
            self.event_generate("<<ConnectionLost>>")

    def _handle_event_threadsafe(self, event: ClientEvent):
        self._client_events.put_nowait(event)
        self.event_generate("<<ClientEvent>>")

    def _on_client_event(self, event: Event) -> None:
        self._handle_event(self._client_events.get_nowait())

    def _handle_event(self, event: ClientEvent) -> None:
        if isinstance(event, ClientEventIncompatibleVersion):
            message = (
                f"The server's protocol version does not match our client version. "
                f"We require V{event.client_version}, but the server "
                f"requires V{event.server_version}."
            )
            messagebox.showerror("Incompatible Version", message)
        elif isinstance(event, ClientEventAuthentication):
            if not event.success:
                message = (
                    "There was an issue connecting to the server. "
                    "Maybe your nickname was taken?"
                )
                messagebox.showerror("Authentication Interrupted", message)
                return

            from .chat_frame import ChatFrame

            self.switch_frame(ChatFrame(self))
            self.submit(self.client.list_channels())

        if isinstance(self.frame, Dispachable):
            self.frame.handle_client_event(event)

    def _on_connection_lost(self, event: Event) -> None:
        exc = self._last_connection_exc
        if exc is None:
            log.info("Disconnected from server")
            messagebox.showwarning(
                "Connection Lost",
                "We have been disconnected by the server.",
            )
        elif isinstance(exc, asyncio.CancelledError):
            # The user wants to close the GUI
            return
        elif (
            isinstance(exc, BaseExceptionGroup)
            and exc.subgroup(AuthenticationFailedError) is not None
        ):
            # Handled via ClientEventAuthentication
            return
        elif isinstance(exc, ConnectionResetError) and reset_during_ssl_handshake(exc):
            log.error("Lost connection during SSL handshake", exc_info=exc)
            messagebox.showerror(
                "Connection Lost",
                "The server closed our connection during the SSL handshake. "
                "Maybe the server does not use SSL?",
            )
        else:
            log.error("Lost connection with server", exc_info=exc)
            messagebox.showerror("Connection Lost", str(exc))

        from .connect_frame import ConnectFrame

        if not isinstance(self.frame, ConnectFrame):
            self.switch_frame(ConnectFrame(self))


def log_fut_exception(fut: concurrent.futures.Future) -> None:
    if fut.cancelled():
        return

    exc = fut.exception()
    if exc is not None:
        log.error("Uncaught exception from future %r", fut, exc_info=exc)


@runtime_checkable
class Dispachable(Protocol):
    def handle_client_event(self, event: ClientEvent) -> Any: ...
