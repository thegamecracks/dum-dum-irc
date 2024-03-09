from enum import Enum

from dumdum.protocol.constants import MAX_MESSAGE_LENGTH, MAX_NICK_LENGTH
from dumdum.protocol.enums import ClientMessageType
from dumdum.protocol.errors import InvalidStateError
from dumdum.protocol.interfaces import Protocol
from dumdum.protocol.reader import Reader, bytearray_reader

from .events import (
    ServerEvent,
    ServerEventAuthenticated,
    ServerEventIncompatibleVersion,
    ServerEventMessageReceived,
)
from .messages import (
    ServerMessageAcknowledgeAuthentication,
    ServerMessagePost,
    ServerMessageSendIncompatibleVersion,
)

ParsedData = tuple[list[ServerEvent], bytes]


class ServerState(Enum):
    AWAITING_AUTHENTICATION = 0
    READY = 1


class Server(Protocol):
    """The server for a single client."""

    PROTOCOL_VERSION = 0

    nick: str | None

    def __init__(self) -> None:
        self.nick = None
        self._buffer = bytearray()
        self._state = ServerState.AWAITING_AUTHENTICATION

    def receive_bytes(self, data: bytes) -> ParsedData:
        self._buffer.extend(data)
        return self._maybe_parse_buffer()

    def send_message(self, nick: str, content: str) -> bytes:
        return bytes(ServerMessagePost(nick, content))

    def _assert_state(self, *states: ServerState) -> None:
        if self._state not in states:
            raise InvalidStateError(self._state, states)

    def _maybe_parse_buffer(self) -> ParsedData:
        full_events: list[ServerEvent] = []
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
        t = ClientMessageType(reader.readexactly(1)[0])
        if t == ClientMessageType.AUTHENTICATE:
            return self._authenticate(reader)
        elif t == ClientMessageType.SEND_MESSAGE:
            return self._send_message(reader)

        raise RuntimeError(f"No handler for {t}")

    def _authenticate(self, reader: Reader) -> ParsedData:
        self._assert_state(ServerState.AWAITING_AUTHENTICATION)

        version = reader.readexactly(1)[0]
        nick = reader.read_varchar(max_length=MAX_NICK_LENGTH)

        if version != self.PROTOCOL_VERSION:
            event = ServerEventIncompatibleVersion(version)
            response = ServerMessageSendIncompatibleVersion(self.PROTOCOL_VERSION)
            return [event], bytes(response)

        # TODO: check that nickname is available

        event = ServerEventAuthenticated(nick=nick)
        response = ServerMessageAcknowledgeAuthentication(success=True)
        self.nick = nick
        self._state = ServerState.READY
        return [event], bytes(response)

    def _send_message(self, reader: Reader) -> ParsedData:
        self._assert_state(ServerState.READY)
        content = reader.read_varchar(max_length=MAX_MESSAGE_LENGTH)

        event = ServerEventMessageReceived(content)
        # TODO: broadcast message to all users
        assert self.nick is not None
        return [event], self.send_message(self.nick, content)
