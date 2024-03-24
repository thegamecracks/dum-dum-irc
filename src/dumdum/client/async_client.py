import asyncio
import contextlib
import ssl
from typing import Any, AsyncIterator, Callable, Self

from dumdum.protocol import (
    Client,
    ClientEvent,
    ClientEventAuthentication,
    ClientEventHello,
    ClientEventIncompatibleVersion,
)

from .errors import (
    AuthenticationFailedError,
    ClientCannotUpgradeSSLError,
    ServerCannotUpgradeSSLError,
)


def maybe_create_fut(last: asyncio.Future | None) -> asyncio.Future:
    if last is None:
        return asyncio.get_running_loop().create_future()
    return last


class AsyncClient:
    _reader: asyncio.StreamReader | None
    _writer: asyncio.StreamWriter | None
    _read_task: asyncio.Task | None
    _addr: str | None
    _auth_fut: asyncio.Future[bool | None] | None
    _ssl_context: ssl.SSLContext | None

    def __init__(
        self,
        nick: str,
        *,
        event_callback: Callable[[ClientEvent], Any],
    ) -> None:
        self.nick = nick
        self.event_callback = event_callback

        self._protocol = Client(nick)
        self._reader = None
        self._writer = None
        self._read_task = None
        self._addr = None

        self._auth_fut = None
        self._ssl_context = None

    @property
    def addr(self) -> str:
        if self._addr is None:
            raise RuntimeError("addr is not yet defined")
        return self._addr

    @contextlib.asynccontextmanager
    async def connect(
        self,
        host: str,
        port: int,
        *,
        ssl: ssl.SSLContext | None,
    ) -> AsyncIterator[Self]:
        self._addr = f"{host}:{port}"  # FIXME: must be canonicalized
        self._auth_fut = maybe_create_fut(self._auth_fut)
        self._ssl_context = ssl
        try:
            self._reader, self._writer = await asyncio.open_connection(host, port)
        except BaseException:
            self._set_authentication(None)
            raise

        async with asyncio.TaskGroup() as tg:
            _read_coro = self._read_loop(self._reader, self._writer)
            self._read_task = tg.create_task(_read_coro)
            self._read_task.add_done_callback(self._on_read_task_done)

            try:
                success = await self._handshake()
                if not success:
                    raise AuthenticationFailedError()

                yield self
            finally:
                await self.close()

    async def run_forever(self) -> None:
        assert self._read_task is not None
        await self._read_task

    async def close(self) -> None:
        if self._writer is not None:
            self._writer.close()
            await self._writer.wait_closed()

    async def send_message(self, channel_name: str, content: str) -> None:
        data = self._protocol.send_message(channel_name, content)
        await self._send_and_drain(data)

    async def list_channels(self) -> None:
        data = self._protocol.list_channels()
        await self._send_and_drain(data)

    async def list_messages(
        self,
        channel_name: str,
        *,
        before: int | None = None,
        after: int | None = None,
    ) -> None:
        data = self._protocol.list_messages(channel_name, before=before, after=after)
        await self._send_and_drain(data)

    async def _read_loop(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        while True:
            data = await reader.read(1024)
            if len(data) == 0:
                break

            events, outgoing = self._protocol.receive_bytes(data)
            writer.write(outgoing)
            await self._handle_events(events)
            await writer.drain()  # exert backpressure

    def _on_read_task_done(self, task: asyncio.Task) -> None:
        self._set_authentication(None)

    async def _handshake(self) -> bool | None:
        assert self._writer is not None
        data = self._protocol.hello()
        self._writer.write(data)
        return await self._wait_for_authentication()

    async def _wait_for_authentication(self) -> bool | None:
        self._auth_fut = maybe_create_fut(self._auth_fut)
        return await asyncio.shield(self._auth_fut)

    async def _handle_events(self, events: list[ClientEvent]) -> None:
        for event in events:
            await self._handle_event(event)

    async def _handle_event(self, event: ClientEvent) -> None:
        if isinstance(event, ClientEventHello):
            if event.using_ssl:
                await self._upgrade_to_ssl()
            elif self._ssl_context is not None:
                raise ServerCannotUpgradeSSLError()

            assert self._writer is not None
            data = self._protocol.authenticate()
            self._writer.write(data)
        elif isinstance(event, ClientEventIncompatibleVersion):
            assert self._writer is not None
            self._writer.close()
        elif isinstance(event, ClientEventAuthentication):
            self._set_authentication(event.success)
        self._dispatch_event(event)

    async def _upgrade_to_ssl(self) -> None:
        if self._ssl_context is None:
            raise ClientCannotUpgradeSSLError()

        assert self._writer is not None
        await self._writer.start_tls(self._ssl_context)

    def _set_authentication(self, result: bool | None) -> None:
        assert self._auth_fut is not None
        if not self._auth_fut.done():
            self._auth_fut.set_result(result)

    def _dispatch_event(self, event: ClientEvent) -> None:
        self.event_callback(event)

    async def _send_and_drain(self, data: bytes) -> None:
        assert self._writer is not None
        self._writer.write(data)
        await self._writer.drain()
