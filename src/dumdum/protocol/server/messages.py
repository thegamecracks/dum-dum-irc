from dataclasses import dataclass
from typing import Sequence

from dumdum.protocol import varchar
from dumdum.protocol.channel import Channel
from dumdum.protocol.constants import (
    MAX_LIST_CHANNEL_LENGTH_BYTES,
    MAX_MESSAGE_LENGTH,
    MAX_NICK_LENGTH,
)
from dumdum.protocol.enums import ServerMessageType


@dataclass
class ServerMessageSendIncompatibleVersion:
    required: int

    def __bytes__(self) -> bytes:
        return bytes(
            [
                ServerMessageType.INCOMPATIBLE_VERSION.value,
                self.required,
            ]
        )


@dataclass
class ServerMessageAcknowledgeAuthentication:
    success: bool

    def __bytes__(self) -> bytes:
        return bytes(
            [
                ServerMessageType.ACKNOWLEDGE_AUTHENTICATION.value,
                self.success,
            ]
        )


@dataclass
class ServerMessagePost:
    channel: Channel
    nick: str
    content: str

    def __bytes__(self) -> bytes:
        return bytes(
            [
                ServerMessageType.SEND_MESSAGE.value,
                *bytes(self.channel),
                *varchar.dumps(self.nick, max_length=MAX_NICK_LENGTH),
                *varchar.dumps(self.content, max_length=MAX_MESSAGE_LENGTH),
            ]
        )


@dataclass
class ServerMessageListChannels:
    channels: Sequence[Channel]

    def __bytes__(self) -> bytes:
        channel_bytes = b"".join(bytes(c) for c in self.channels)
        channel_length = len(channel_bytes).to_bytes(
            MAX_LIST_CHANNEL_LENGTH_BYTES,
            byteorder="big",
        )
        return bytes(
            [
                ServerMessageType.LIST_CHANNELS.value,
                *channel_length,
                *channel_bytes,
            ]
        )
