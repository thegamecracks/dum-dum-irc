from enum import Enum, auto
from typing import Sequence

from dumdum.protocol.buffer import extend_limited_buffer
from dumdum.protocol.channel import Channel
from dumdum.protocol.constants import (
    MAX_CHANNEL_NAME_LENGTH,
    MAX_MESSAGE_LENGTH,
    MAX_NICK_LENGTH,
)
from dumdum.protocol.enums import ClientMessageType
from dumdum.protocol.errors import InvalidStateError, MalformedDataError
from dumdum.protocol.interfaces import Protocol
from dumdum.protocol.message import Message
from dumdum.protocol.reader import Reader, bytearray_reader

from .events import (
    ServerEvent,
    ServerEventAuthentication,
    ServerEventHello,
    ServerEventIncompatibleVersion,
    ServerEventListChannels,
    ServerEventListMessages,
    ServerEventMessageReceived,
)
from .messages import (
    ServerMessageAcknowledgeAuthentication,
    ServerMessageHello,
    ServerMessageListChannels,
    ServerMessageListMessages,
    ServerMessagePost,
    ServerMessageSendIncompatibleVersion,
)

ParsedData = tuple[list[ServerEvent], bytes]


class ServerState(Enum):
    AWAITING_CLIENT_HELLO = auto()
    AWAITING_SERVER_HELLO = auto()
    AWAITING_AUTHENTICATION = auto()
    READY = auto()


class Server(Protocol):
    """The server for a single client."""

    PROTOCOL_VERSION = 2

    def __init__(self, *, buffer_size: int | None = 2**20) -> None:
        self.buffer_size = buffer_size

        self._buffer = bytearray()
        self._state = ServerState.AWAITING_CLIENT_HELLO

    def receive_bytes(self, data: bytes) -> ParsedData:
        extend_limited_buffer(self._buffer, data, limit=self.buffer_size)
        return self._maybe_parse_buffer()

    def hello(self, *, using_ssl: bool) -> bytes:
        self._assert_state(ServerState.AWAITING_SERVER_HELLO)
        self._state = ServerState.AWAITING_AUTHENTICATION
        return bytes(ServerMessageHello(using_ssl))

    def authenticate(self, *, success: bool) -> bytes:
        self._assert_state(ServerState.AWAITING_AUTHENTICATION)

        if success:
            self._state = ServerState.READY

        return bytes(ServerMessageAcknowledgeAuthentication(success))

    def send_message(self, message: Message) -> bytes:
        self._assert_state(ServerState.READY)
        return bytes(ServerMessagePost(message))

    def list_channels(self, channels: Sequence[Channel]) -> bytes:
        return bytes(ServerMessageListChannels(channels))

    def list_messages(self, messages: Sequence[Message]) -> bytes:
        return bytes(ServerMessageListMessages(messages))

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
        except (IndexError, ValueError) as e:
            # FIXME: this is making stuff hard to debug...
            if isinstance(e, UnicodeDecodeError):
                raise MalformedDataError(str(e)) from e

        return full_events, bytes(full_outgoing)

    def _read_message(self, reader: Reader) -> ParsedData:
        n = reader.readexactly(1)[0]
        try:
            t = ClientMessageType(n)
        except ValueError:
            raise MalformedDataError(f"Unknown message type {n}") from None

        if t == ClientMessageType.HELLO:
            return self._parse_hello(reader)
        elif t == ClientMessageType.AUTHENTICATE:
            return self._authenticate(reader)
        elif t == ClientMessageType.SEND_MESSAGE:
            return self._send_message(reader)
        elif t == ClientMessageType.LIST_CHANNELS:
            return self._list_channels(reader)
        elif t == ClientMessageType.LIST_MESSAGES:
            return self._list_messages(reader)

        raise RuntimeError(f"No handler for {t}")  # pragma: no cover

    def _parse_hello(self, reader: Reader) -> ParsedData:
        self._assert_state(ServerState.AWAITING_CLIENT_HELLO)

        version = reader.readexactly(1)[0]
        if version != self.PROTOCOL_VERSION:
            event = ServerEventIncompatibleVersion(version)
            response = ServerMessageSendIncompatibleVersion(self.PROTOCOL_VERSION)
            return [event], bytes(response)

        event = ServerEventHello()
        self._state = ServerState.AWAITING_SERVER_HELLO
        return [event], b""

    def _authenticate(self, reader: Reader) -> ParsedData:
        self._assert_state(ServerState.AWAITING_AUTHENTICATION)
        nick = reader.read_varchar(max_length=MAX_NICK_LENGTH)
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

    def _list_messages(self, reader: Reader) -> ParsedData:
        self._assert_state(ServerState.READY)
        channel_name = reader.read_varchar(max_length=MAX_CHANNEL_NAME_LENGTH)
        before = reader.read_bigint() or None
        after = reader.read_bigint() or None
        event = ServerEventListMessages(channel_name, before, after)
        return [event], b""
