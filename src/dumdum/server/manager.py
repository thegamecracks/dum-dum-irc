import asyncio
import contextlib
import logging
import ssl

from dumdum.protocol import (
    InvalidStateError,
    Message,
    Server,
    ServerEvent,
    ServerEventAuthentication,
    ServerEventHello,
    ServerEventListChannels,
    ServerEventListMessages,
    ServerEventMessageReceived,
    create_snowflake,
)

from .connection import Connection
from .state import ServerState

log = logging.getLogger(__name__)


class Manager:
    def __init__(
        self,
        state: ServerState,
        ssl: ssl.SSLContext | None,
        *,
        drain_timeout: float = 30,
        close_timeout: float = 5,
    ) -> None:
        self.state = state
        self.connections: list[Connection] = []
        self.ssl = ssl
        self.drain_timeout = drain_timeout
        self.close_timeout = close_timeout

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
        except asyncio.CancelledError:
            # Don't need to log this exception
            asyncio.current_task().uncancel()  # type: ignore
        except ConnectionResetError:
            # Client wants to disconnect
            pass
        except BaseException:
            log.exception("Error occurred while handling %s", addr)
        finally:
            log.info("Connection %s has disconnected", addr)

            writer.close()
            await self._wait_closed(writer)

            self._close_connection(connection)

    def _create_server(self) -> Server:
        return Server()

    async def _wait_closed(self, writer: asyncio.StreamWriter) -> None:
        timeout = self.close_timeout
        with contextlib.suppress(Exception):
            await asyncio.wait_for(writer.wait_closed(), timeout=timeout)

    async def _handle_events(self, conn: Connection, events: list[ServerEvent]) -> None:
        for event in events:
            await self._handle_event(conn, event)

    async def _handle_event(self, conn: Connection, event: ServerEvent) -> None:
        log.debug(
            "%s produced by %s",
            type(event).__name__,
            conn.writer.get_extra_info("peername"),
        )

        if isinstance(event, ServerEventHello):
            await self._hello(conn, event)
        elif isinstance(event, ServerEventAuthentication):
            self._authenticate(conn, event)
        elif isinstance(event, ServerEventMessageReceived):
            self._broadcast_message(conn, event)
        elif isinstance(event, ServerEventListChannels):
            self._list_channels(conn, event)
        elif isinstance(event, ServerEventListMessages):
            self._list_messages(conn, event)

    async def _hello(self, conn: Connection, event: ServerEventHello) -> None:
        using_ssl = self.ssl is not None

        data = conn.server.hello(using_ssl=using_ssl)
        conn.writer.write(data)

        if using_ssl:
            assert self.ssl is not None
            await conn.writer.start_tls(self.ssl)

    def _authenticate(self, conn: Connection, event: ServerEventAuthentication) -> None:
        user = self.state.get_user(event.nick)
        if user is None:
            self.state.add_user(event.nick)
            conn.nick = event.nick
            success = True
        else:
            success = False

        data = conn.server.authenticate(success=success)
        conn.writer.write(data)

    def _broadcast_message(
        self,
        conn: Connection,
        event: ServerEventMessageReceived,
    ) -> None:
        assert conn.nick is not None

        if self.state.get_channel(event.channel_name) is None:
            return

        message = Message(
            create_snowflake(),
            event.channel_name,
            conn.nick,
            event.content,
        )
        self.state.add_message(message)

        for peer in self.connections:
            with contextlib.suppress(InvalidStateError):
                data = peer.server.send_message(message)
                peer.writer.write(data)

    def _list_channels(self, conn: Connection, event: ServerEventListChannels) -> None:
        data = conn.server.list_channels(self.state.channels)
        conn.writer.write(data)

    def _list_messages(self, conn: Connection, event: ServerEventListMessages) -> None:
        messages = self.state.get_messages(
            event.channel_name,
            before=event.before,
            after=event.after,
        )
        data = conn.server.list_messages(messages)
        conn.writer.write(data)

    def _close_connection(self, conn: Connection) -> None:
        self.connections.remove(conn)
        if conn.nick is not None:
            self.state.remove_user(conn.nick)


async def host_server(
    state: ServerState,
    host: str | None,
    port: int,
    *,
    ssl: ssl.SSLContext | None,
) -> None:
    manager = Manager(state, ssl)
    server = await asyncio.start_server(
        manager.accept_connection,
        host=host,
        port=port,
    )
    async with server:
        await server.serve_forever()
