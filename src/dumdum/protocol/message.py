from dataclasses import dataclass
from typing import Self

from . import varchar
from .constants import MAX_CHANNEL_NAME_LENGTH, MAX_MESSAGE_LENGTH, MAX_NICK_LENGTH
from .reader import Reader


@dataclass
class Message:
    id: int
    channel_name: str
    nick: str
    content: str

    def __bytes__(self) -> bytes:
        return bytes(
            [
                *self.id.to_bytes(8, byteorder="big"),
                *varchar.dumps(self.channel_name, max_length=MAX_CHANNEL_NAME_LENGTH),
                *varchar.dumps(self.nick, max_length=MAX_NICK_LENGTH),
                *varchar.dumps(self.content, max_length=MAX_MESSAGE_LENGTH),
            ]
        )

    @classmethod
    def from_reader(cls, reader: Reader) -> Self:
        id = reader.read_bigint()
        channel_name = reader.read_varchar(max_length=MAX_CHANNEL_NAME_LENGTH)
        nick = reader.read_varchar(max_length=MAX_NICK_LENGTH)
        content = reader.read_varchar(max_length=MAX_MESSAGE_LENGTH)
        return cls(id=id, channel_name=channel_name, nick=nick, content=content)
