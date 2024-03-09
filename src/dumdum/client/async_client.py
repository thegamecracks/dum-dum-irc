import asyncio
import contextlib
from typing import Any, AsyncIterator, Callable, Self

from dumdum.protocol import (
    Client,
    ClientEvent,
    ClientEventAuthentication,
    ClientEventIncompatibleVersion,
)


class AsyncClient:
    _reader: asyncio.StreamReader | None
    _writer: asyncio.StreamWriter | None
    _read_task: asyncio.Task | None
    _auth_fut: asyncio.Future[bool] | None

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

        self._auth_fut = None

    @contextlib.asynccontextmanager
    async def connect(self, host: str, port: int) -> AsyncIterator[Self]:
        self._reader, self._writer = await asyncio.open_connection(host, port)
        async with asyncio.TaskGroup() as tg:
            _read_coro = self._read_loop(self._reader, self._writer)
            self._read_task = tg.create_task(_read_coro)

            try:
                success = await self._handshake()
                if not success:
                    raise RuntimeError("Could not authenticate with server")

                yield self
            finally:
                await self.close()

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
            self._handle_events(events)
            await writer.drain()  # exert backpressure

    async def _handshake(self) -> bool:
        assert self._writer is not None
        data = self._protocol.authenticate()
        self._writer.write(data)
        return await self._wait_for_authentication()

    async def _wait_for_authentication(self) -> bool:
        assert self._auth_fut is None
        self._auth_fut = asyncio.get_running_loop().create_future()
        return await self._auth_fut

    def _handle_events(self, events: list[ClientEvent]) -> None:
        for event in events:
            self._handle_event(event)

    def _handle_event(self, event: ClientEvent) -> None:
        if isinstance(event, ClientEventIncompatibleVersion):
            assert self._writer is not None
            self._writer.close()
        if isinstance(event, ClientEventAuthentication):
            self._set_authentication(event.success)
        self._dispatch_event(event)

    def _set_authentication(self, success: bool) -> None:
        assert self._auth_fut is not None
        self._auth_fut.set_result(success)

    def _dispatch_event(self, event: ClientEvent) -> None:
        self.event_callback(event)

    async def _send_and_drain(self, data: bytes) -> None:
        assert self._writer is not None
        self._writer.write(data)
        await self._writer.drain()
