import math
from io import BytesIO
from typing import Protocol

from .errors import InvalidLengthError


class _Readable(Protocol):
    def read(self, n: int, /) -> bytes: ...


def load(f: _Readable, *, max_length: int) -> str:
    byte_count = math.ceil(max_length.bit_length() / 8)
    length_bytes = f.read(byte_count)
    if len(length_bytes) != byte_count:
        raise ValueError(f"Insufficient bytes for {max_length = }")

    length = int.from_bytes(length_bytes, byteorder="big")
    if length > max_length:
        raise InvalidLengthError(length, max_length)

    message = f.read(length)
    if length != len(message):
        raise ValueError(f"Insufficient bytes for {max_length = }")

    return message.decode()


def loads(message: bytes, *, max_length: int) -> str:
    return load(BytesIO(message), max_length=max_length)


def dumps(message: str, *, max_length: int) -> bytes:
    message_bytes = message.encode()
    byte_count = math.ceil(max_length.bit_length() / 8)
    length = len(message_bytes).to_bytes(byte_count, byteorder="big")
    return length + message_bytes
