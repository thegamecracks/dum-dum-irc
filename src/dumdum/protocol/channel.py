from dataclasses import dataclass, field
from typing import Self

from . import varchar
from .constants import MAX_CHANNEL_NAME_LENGTH
from .reader import Reader


@dataclass
class Channel:
    name: str = field(hash=True)

    def __bytes__(self) -> bytes:
        return varchar.dumps(self.name, max_length=MAX_CHANNEL_NAME_LENGTH)

    @classmethod
    def from_reader(cls, reader: Reader) -> Self:
        name = reader.read_varchar(max_length=MAX_CHANNEL_NAME_LENGTH)
        return cls(name=name)
