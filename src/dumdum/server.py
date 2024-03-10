"""Host a dumdum server."""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import logging

from dumdum.logging import configure_logging
from dumdum.protocol import (
    Channel,
    HighCommand,
    InvalidStateError,
    Server,
    ServerEvent,
    ServerEventMessageReceived,
)

log = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase logging verbosity",
    )
    parser.add_argument(
        "-c",
        "--channels",
        action="extend",
        nargs="+",
        help="A list of channels",
        type=parse_channel,
    )
    parser.add_argument(
        "--host",
        default=None,
        help="The address to host on",
    )
    parser.add_argument(
        "--port",
        default=6667,
        help="The port number to host on",
    )

    args = parser.parse_args()
    verbose: int = args.verbose
    channels: list[Channel] = args.channels or get_default_channels()
    host: str | None = args.host
    port: int = args.port

    configure_logging(verbose)

    hc = HighCommand()
    for channel in channels:
        hc.add_channel(channel)

    try:
        asyncio.run(host_server(hc, host, port))
    except KeyboardInterrupt:
        pass


def parse_channel(s: str) -> Channel:
    return Channel(name=s)


def get_default_channels() -> list[Channel]:
    return [Channel("general")]


async def host_server(
    hc: HighCommand,
    host: str | None,
    port: int,
) -> None:
    manager = Manager(hc)
    server = await asyncio.start_server(
        manager.accept_connection,
        host=host,
        port=port,
    )
    async with server:
        await server.serve_forever()


class Manager:
    def __init__(self, hc: HighCommand) -> None:
        self.hc = hc
        self.connections: list[Connection] = []

    async def accept_connection(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ):
        addr = writer.get_extra_info("peername")
        log.info("Accepted connection from %s", addr)

        connection = Connection(self, reader, writer, self._create_server())
        self.connections.append(connection)
        try:
            await connection.communicate()
        except BaseException:
            log.exception("Error occurred while handling %s", addr)
        finally:
            log.info("Connection %s has disconnected", addr)
            writer.close()
            await writer.wait_closed()
            self.connections.remove(connection)

    def _create_server(self) -> Server:
        return Server(self.hc)

    def _handle_events(self, conn: Connection, events: list[ServerEvent]) -> None:
        for event in events:
            self._handle_event(conn, event)

    def _handle_event(self, conn: Connection, event: ServerEvent) -> None:
        log.debug(
            "%s produced by %s",
            type(event).__name__,
            conn.writer.get_extra_info("peername"),
        )

        if isinstance(event, ServerEventMessageReceived):
            self._broadcast_message(conn, event)

    def _broadcast_message(
        self,
        conn: Connection,
        event: ServerEventMessageReceived,
    ) -> None:
        assert conn.server.nick is not None
        for peer in self.connections:
            with contextlib.suppress(InvalidStateError):
                data = peer.server.send_message(
                    event.channel,
                    conn.server.nick,
                    event.content,
                )
                peer.writer.write(data)


class Connection:
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

    async def communicate(self) -> None:
        try:
            while True:
                data = await self.reader.read(1024)
                if len(data) == 0:
                    break

                events, outgoing = self.server.receive_bytes(data)
                self.writer.write(outgoing)
                self._handle_events(events)
                await self.writer.drain()  # exert backpressure
        finally:
            self.server.close()

    def _handle_events(self, events: list[ServerEvent]) -> None:
        self.manager._handle_events(self, events)


if __name__ == "__main__":
    main()
