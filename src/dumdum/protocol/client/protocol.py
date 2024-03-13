from enum import Enum

from dumdum.protocol.channel import Channel
from dumdum.protocol.constants import (
    MAX_LIST_CHANNEL_LENGTH_BYTES,
    MAX_LIST_MESSAGE_LENGTH_BYTES,
)
from dumdum.protocol.enums import ServerMessageType
from dumdum.protocol.errors import InvalidStateError, MalformedDataError
from dumdum.protocol.interfaces import Protocol
from dumdum.protocol.message import Message
from dumdum.protocol.reader import Reader, byte_reader, bytearray_reader

from .events import (
    ClientEvent,
    ClientEventAuthentication,
    ClientEventChannelsListed,
    ClientEventIncompatibleVersion,
    ClientEventMessageReceived,
    ClientEventMessagesListed,
)
from .messages import (
    ClientMessageAuthenticate,
    ClientMessageListChannels,
    ClientMessageListMessages,
    ClientMessagePost,
)

ParsedData = tuple[list[ClientEvent], bytes]


class ClientState(Enum):
    AWAITING_AUTHENTICATION = 0
    READY = 1


class Client(Protocol):
    """The client connected to a server."""

    PROTOCOL_VERSION = 1

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
                version=self.PROTOCOL_VERSION,
                nick=self.nick,
            )
        )

    def send_message(self, channel_name: str, content: str) -> bytes:
        self._assert_state(ClientState.READY)
        return bytes(ClientMessagePost(channel_name, content))

    def list_channels(self) -> bytes:
        self._assert_state(ClientState.READY)
        return bytes(ClientMessageListChannels())

    def list_messages(
        self,
        channel_name: str,
        *,
        before: int | None = None,
        after: int | None = None,
    ) -> bytes:
        self._assert_state(ClientState.READY)

        if before is not None and before < 1:
            raise ValueError(f"before must be 1 or greater, not {before}")
        if after is not None and after < 1:
            raise ValueError(f"after must be 1 or greater, not {after}")

        return bytes(ClientMessageListMessages(channel_name, before, after))

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
        except (IndexError, ValueError) as e:
            # FIXME: this is making stuff hard to debug...
            if isinstance(e, UnicodeDecodeError):
                raise MalformedDataError(str(e)) from e

        return full_events, bytes(full_outgoing)

    def _read_message(self, reader: Reader) -> ParsedData:
        n = reader.readexactly(1)[0]
        try:
            t = ServerMessageType(n)
        except ValueError:
            raise MalformedDataError(f"Unknown message type {n}") from None

        if t == ServerMessageType.INCOMPATIBLE_VERSION:
            return self._parse_incompatible_version(reader)
        elif t == ServerMessageType.ACKNOWLEDGE_AUTHENTICATION:
            return self._accept_authentication(reader)
        elif t == ServerMessageType.SEND_MESSAGE:
            return self._parse_message(reader)
        elif t == ServerMessageType.LIST_CHANNELS:
            return self._parse_channel_list(reader)
        elif t == ServerMessageType.LIST_MESSAGES:
            return self._parse_message_list(reader)

        raise RuntimeError(f"No handler for {t}")  # pragma: no cover

    def _parse_incompatible_version(self, reader: Reader) -> ParsedData:
        self._assert_state(ClientState.AWAITING_AUTHENTICATION)
        version = reader.readexactly(1)[0]
        event = ClientEventIncompatibleVersion(version, self.PROTOCOL_VERSION)
        return [event], b""

    def _accept_authentication(self, reader: Reader) -> ParsedData:
        self._assert_state(ClientState.AWAITING_AUTHENTICATION)

        success = reader.readexactly(1)[0] > 0
        if success:
            self._state = ClientState.READY

        event = ClientEventAuthentication(success)
        return [event], b""

    def _parse_message(self, reader: Reader) -> ParsedData:
        self._assert_state(ClientState.READY)
        message = Message.from_reader(reader)
        event = ClientEventMessageReceived(message)
        return [event], b""

    def _parse_channel_list(self, reader: Reader) -> ParsedData:
        self._assert_state(ClientState.READY)
        length = int.from_bytes(
            reader.readexactly(MAX_LIST_CHANNEL_LENGTH_BYTES),
            byteorder="big",
        )
        channel_bytes = reader.readexactly(length)

        channels: list[Channel] = []
        with byte_reader(channel_bytes) as channel_reader:
            try:
                while True:
                    channels.append(Channel.from_reader(channel_reader))
            except IndexError:
                pass

        event = ClientEventChannelsListed(channels)
        return [event], b""

    def _parse_message_list(self, reader: Reader) -> ParsedData:
        self._assert_state(ClientState.READY)
        length = int.from_bytes(
            reader.readexactly(MAX_LIST_MESSAGE_LENGTH_BYTES),
            byteorder="big",
        )
        message_bytes = reader.readexactly(length)

        messages: list[Message] = []
        with byte_reader(message_bytes) as message_reader:
            try:
                while True:
                    messages.append(Message.from_reader(message_reader))
            except IndexError:
                pass

        event = ClientEventMessagesListed(messages)
        return [event], b""
