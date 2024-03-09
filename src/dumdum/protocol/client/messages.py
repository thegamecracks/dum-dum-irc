from dataclasses import dataclass

from dumdum.protocol import varchar
from dumdum.protocol.constants import (
    MAX_CHANNEL_NAME_LENGTH,
    MAX_MESSAGE_LENGTH,
    MAX_NICK_LENGTH,
)
from dumdum.protocol.enums import ClientMessageType


@dataclass
class ClientMessageAuthenticate:
    version: int
    nick: str

    def __bytes__(self) -> bytes:
        return bytes(
            [
                ClientMessageType.AUTHENTICATE.value,
                self.version,
                *varchar.dumps(self.nick, max_length=MAX_NICK_LENGTH),
            ]
        )


@dataclass
class ClientMessagePost:
    channel_name: str
    content: str

    def __bytes__(self) -> bytes:
        return bytes(
            [
                ClientMessageType.SEND_MESSAGE.value,
                *varchar.dumps(self.channel_name, max_length=MAX_CHANNEL_NAME_LENGTH),
                *varchar.dumps(self.content, max_length=MAX_MESSAGE_LENGTH),
            ]
        )
