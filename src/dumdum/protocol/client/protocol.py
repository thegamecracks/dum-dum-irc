from enum import Enum
from dumdum.protocol.channel import Channel

from dumdum.protocol.constants import (
    MAX_LIST_CHANNEL_LENGTH_BYTES,
    MAX_MESSAGE_LENGTH,
    MAX_NICK_LENGTH,
)
from dumdum.protocol.enums import ServerMessageType
from dumdum.protocol.errors import InvalidStateError
from dumdum.protocol.interfaces import Protocol
from dumdum.protocol.reader import Reader, byte_reader, bytearray_reader

from .events import (
    ClientEvent,
    ClientEventAuthentication,
    ClientEventChannelsListed,
    ClientEventIncompatibleVersion,
    ClientEventMessageReceived,
)
from .messages import ClientMessageAuthenticate, ClientMessageListChannels, ClientMessagePost

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

    def send_message(self, channel_name: str, content: str) -> bytes:
        return bytes(ClientMessagePost(channel_name, content))

    def list_channels(self) -> bytes:
        return bytes(ClientMessageListChannels())

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
            # FIXME: this is making stuff hard to debug...
            pass

        return full_events, bytes(full_outgoing)

    def _read_message(self, reader: Reader) -> ParsedData:
        t = ServerMessageType(reader.readexactly(1)[0])
        if t == ServerMessageType.INCOMPATIBLE_VERSION:
            return self._parse_required_version(reader)
        elif t == ServerMessageType.ACKNOWLEDGE_AUTHENTICATION:
            return self._accept_authentication(reader)
        elif t == ServerMessageType.SEND_MESSAGE:
            return self._parse_message(reader)
        elif t == ServerMessageType.LIST_CHANNELS:
            return self._parse_channel_list(reader)

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

    def _parse_message(self, reader: Reader) -> ParsedData:
        channel = Channel.from_reader(reader)
        nick = reader.read_varchar(max_length=MAX_NICK_LENGTH)
        content = reader.read_varchar(max_length=MAX_MESSAGE_LENGTH)
        event = ClientEventMessageReceived(channel, nick, content)
        return [event], b""

    def _parse_channel_list(self, reader: Reader) -> ParsedData:
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
