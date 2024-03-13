from enum import Enum
from typing import Sequence

from dumdum.protocol.channel import Channel
from dumdum.protocol.constants import (
    MAX_CHANNEL_NAME_LENGTH,
    MAX_MESSAGE_LENGTH,
    MAX_NICK_LENGTH,
)
from dumdum.protocol.enums import ClientMessageType
from dumdum.protocol.errors import InvalidStateError
from dumdum.protocol.interfaces import Protocol
from dumdum.protocol.reader import Reader, bytearray_reader

from .events import (
    ServerEvent,
    ServerEventAuthentication,
    ServerEventIncompatibleVersion,
    ServerEventListChannels,
    ServerEventMessageReceived,
)
from .messages import (
    ServerMessageAcknowledgeAuthentication,
    ServerMessageListChannels,
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

    def __init__(self) -> None:
        self._buffer = bytearray()
        self._state = ServerState.AWAITING_AUTHENTICATION

    def receive_bytes(self, data: bytes) -> ParsedData:
        self._buffer.extend(data)
        return self._maybe_parse_buffer()

    def acknowledge_authentication(self, *, success: bool) -> bytes:
        self._assert_state(ServerState.AWAITING_AUTHENTICATION)

        if success:
            self._state = ServerState.READY

        return bytes(ServerMessageAcknowledgeAuthentication(success))

    def send_message(self, channel_name: str, nick: str, content: str) -> bytes:
        self._assert_state(ServerState.READY)
        return bytes(ServerMessagePost(channel_name, nick, content))

    def list_channels(self, channels: Sequence[Channel]) -> bytes:
        return bytes(ServerMessageListChannels(channels))

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
            # FIXME: this is making stuff hard to debug...
            pass

        return full_events, bytes(full_outgoing)

    def _read_message(self, reader: Reader) -> ParsedData:
        t = ClientMessageType(reader.readexactly(1)[0])
        if t == ClientMessageType.AUTHENTICATE:
            return self._authenticate(reader)
        elif t == ClientMessageType.SEND_MESSAGE:
            return self._send_message(reader)
        elif t == ClientMessageType.LIST_CHANNELS:
            return self._list_channels(reader)

        raise RuntimeError(f"No handler for {t}")

    def _authenticate(self, reader: Reader) -> ParsedData:
        self._assert_state(ServerState.AWAITING_AUTHENTICATION)

        version = reader.readexactly(1)[0]
        nick = reader.read_varchar(max_length=MAX_NICK_LENGTH)

        if version != self.PROTOCOL_VERSION:
            event = ServerEventIncompatibleVersion(version)
            response = ServerMessageSendIncompatibleVersion(self.PROTOCOL_VERSION)
            return [event], bytes(response)

        event = ServerEventAuthentication(nick=nick)
        return [event], b""

    def _send_message(self, reader: Reader) -> ParsedData:
        self._assert_state(ServerState.READY)
        channel_name = reader.read_varchar(max_length=MAX_CHANNEL_NAME_LENGTH)
        content = reader.read_varchar(max_length=MAX_MESSAGE_LENGTH)

        event = ServerEventMessageReceived(channel_name, content)
        # TODO: broadcast message to all users
        return [event], b""

    def _list_channels(self, reader: Reader) -> ParsedData:
        self._assert_state(ServerState.READY)
        event = ServerEventListChannels()
        return [event], b""
