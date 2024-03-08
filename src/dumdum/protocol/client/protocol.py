from enum import Enum

from dumdum.protocol.enums import ServerMessageType
from dumdum.protocol.errors import InvalidStateError
from dumdum.protocol.interfaces import Protocol
from dumdum.protocol.reader import Reader, bytearray_reader

from .events import (
    ClientEvent,
    ClientEventAuthentication,
    ClientEventIncompatibleVersion,
)
from .messages import ClientMessageAuthenticate

ParsedData = tuple[list[ClientEvent], bytes]


class ClientState(Enum):
    AWAITING_AUTHENTICATION = 0
    READY = 1


class Client(Protocol):
    """The client connected to a server."""

    REQUIRED_VERSION = 0

    def __init__(self, nick: str) -> None:
        self.nick = nick

        self._buffer = bytearray()
        self._state = ClientState.AWAITING_AUTHENTICATION

    def receive_bytes(self, data: bytes) -> ParsedData:
        self._buffer.extend(data)
        return self._maybe_parse_buffer()

    def authenticate(self) -> bytes:
        self._assert_state(ClientState.AWAITING_AUTHENTICATION)
        return bytes(
            ClientMessageAuthenticate(
                version=self.REQUIRED_VERSION,
                nick=self.nick,
            )
        )

    def _assert_state(self, *states: ClientState) -> None:
        if self._state not in states:
            raise InvalidStateError(self._state, states)

    def _maybe_parse_buffer(self) -> ParsedData:
        full_events: list[ClientEvent] = []
        full_outgoing = bytearray()

        try:
            while True:
                with bytearray_reader(self._buffer) as reader:
                    events, outgoing = self._read_message(reader)

                full_events.extend(events)
                full_outgoing.extend(outgoing)
        except (IndexError, ValueError):
            pass

        return full_events, bytes(full_outgoing)

    def _read_message(self, reader: Reader) -> ParsedData:
        t = ServerMessageType(reader.readexactly(1)[0])
        if t == ServerMessageType.INCOMPATIBLE_VERSION:
            return self._parse_required_version(reader)
        elif t == ServerMessageType.ACKNOWLEDGE_AUTHENTICATION:
            return self._accept_authentication(reader)

        raise RuntimeError(f"No handler for {t}")

    def _parse_required_version(self, reader: Reader) -> ParsedData:
        self._assert_state(ClientState.AWAITING_AUTHENTICATION)
        version = reader.readexactly(1)[0]
        event = ClientEventIncompatibleVersion(version)
        return [event], b""

    def _accept_authentication(self, reader: Reader) -> ParsedData:
        self._assert_state(ClientState.AWAITING_AUTHENTICATION)

        success = reader.readexactly(1)[0] > 0
        if success:
            self._state = ClientState.READY

        event = ClientEventAuthentication(success)
        return [event], b""
