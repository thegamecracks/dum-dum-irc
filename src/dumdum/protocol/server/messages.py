from dataclasses import dataclass

from dumdum.protocol import varchar
from dumdum.protocol.channel import Channel
from dumdum.protocol.constants import MAX_MESSAGE_LENGTH, MAX_NICK_LENGTH
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
