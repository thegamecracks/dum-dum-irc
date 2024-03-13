from dataclasses import dataclass
from typing import Sequence

from dumdum.protocol.channel import Channel
from dumdum.protocol.constants import (
    MAX_LIST_CHANNEL_LENGTH_BYTES,
    MAX_LIST_MESSAGE_LENGTH_BYTES,
)
from dumdum.protocol.enums import ServerMessageType
from dumdum.protocol.message import Message


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
    message: Message

    def __bytes__(self) -> bytes:
        return bytes(
            [
                ServerMessageType.SEND_MESSAGE.value,
                *bytes(self.message),
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


@dataclass
class ServerMessageListMessages:
    messages: Sequence[Message]

    def __bytes__(self) -> bytes:
        message_bytes = b"".join(bytes(c) for c in self.messages)
        message_length = len(message_bytes).to_bytes(
            MAX_LIST_MESSAGE_LENGTH_BYTES,
            byteorder="big",
        )
        return bytes(
            [
                ServerMessageType.LIST_MESSAGES.value,
                *message_length,
                *message_bytes,
            ]
        )
