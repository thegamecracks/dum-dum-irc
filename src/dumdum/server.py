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
    Message,
    Server,
    ServerEvent,
    ServerEventAuthentication,
    ServerEventListChannels,
    ServerEventMessageReceived,
    create_snowflake,
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
            self._close_connection(connection)

    def _create_server(self) -> Server:
        return Server()

    def _handle_events(self, conn: Connection, events: list[ServerEvent]) -> None:
        for event in events:
            self._handle_event(conn, event)

    def _handle_event(self, conn: Connection, event: ServerEvent) -> None:
        log.debug(
            "%s produced by %s",
            type(event).__name__,
            conn.writer.get_extra_info("peername"),
        )

        if isinstance(event, ServerEventAuthentication):
            self._authenticate(conn, event)
        elif isinstance(event, ServerEventMessageReceived):
            self._broadcast_message(conn, event)
        elif isinstance(event, ServerEventListChannels):
            self._list_channels(conn, event)

    def _authenticate(self, conn: Connection, event: ServerEventAuthentication) -> None:
        user = self.hc.get_user(event.nick)
        if user is None:
            self.hc.add_user(event.nick)
            conn.nick = event.nick
            success = True
        else:
            success = False

        data = conn.server.acknowledge_authentication(success=success)
        conn.writer.write(data)

    def _broadcast_message(
        self,
        conn: Connection,
        event: ServerEventMessageReceived,
    ) -> None:
        assert conn.nick is not None

        if self.hc.get_channel(event.channel_name) is None:
            return

        message = Message(
            create_snowflake(),
            event.channel_name,
            conn.nick,
            event.content,
        )
        self.hc.add_message(message)

        for peer in self.connections:
            with contextlib.suppress(InvalidStateError):
                data = peer.server.send_message(message)
                peer.writer.write(data)

    def _list_channels(self, conn: Connection, event: ServerEventListChannels) -> None:
        data = conn.server.list_channels(self.hc.channels)
        conn.writer.write(data)

    def _close_connection(self, conn: Connection) -> None:
        self.connections.remove(conn)
        if conn.nick is not None:
            self.hc.remove_user(conn.nick)


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
            self._handle_events(events)
            await self.writer.drain()  # exert backpressure

    def _handle_events(self, events: list[ServerEvent]) -> None:
        self.manager._handle_events(self, events)


if __name__ == "__main__":
    main()
