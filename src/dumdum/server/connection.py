from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from dumdum.protocol import Server, ServerEvent

if TYPE_CHECKING:
    from .manager import Manager


class Connection:
    nick: str | None

    def __init__(
        self,
        manager: Manager,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        server: Server,
    ):
        self.manager = manager
        self.reader = reader
        self.writer = writer
        self.server = server

        self.nick = None

    async def communicate(self) -> None:
        while True:
            data = await self.reader.read(1024)
            if len(data) == 0:
                break

            events, outgoing = self.server.receive_bytes(data)
            self.writer.write(outgoing)
            await self._handle_events(events)
            await self.writer.drain()  # exert backpressure

    async def _handle_events(self, events: list[ServerEvent]) -> None:
        await self.manager._handle_events(self, events)
