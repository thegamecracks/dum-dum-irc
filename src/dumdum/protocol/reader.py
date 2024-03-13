import contextlib
from typing import Iterator

from dumdum.protocol import varchar


class Reader:
    def __init__(self, buffer: bytearray | bytes) -> None:
        self.buffer = buffer
        self._index = 0
        self._closed = False

    def read(self, n: int = -1) -> bytes:
        if self._closed:
            raise RuntimeError("Cannot read from closed reader")

        if n < 0:
            n = len(self.buffer)
        else:
            n = min(n, len(self.buffer))

        start, self._index = self._index, self._index + n
        return self.buffer[start : self._index]

    def readexactly(self, n: int) -> bytes:
        if n < 0:
            raise ValueError(f"n must be 0 or greater, not {n}")

        data = self.read(n)
        if len(data) != n:
            raise IndexError(
                f"Insufficent data to read (expected {n}, got {len(data)})"
            )

        return data

    def read_bigint(self) -> int:
        data = self.readexactly(8)
        return int.from_bytes(data, byteorder="big")

    def read_varchar(self, *, max_length: int) -> str:
        return varchar.load(self, max_length=max_length)

    def close(self) -> None:
        self._closed = True


@contextlib.contextmanager
def bytearray_reader(buffer: bytearray) -> Iterator[Reader]:
    reader = Reader(buffer)

    try:
        yield reader
    finally:
        reader.close()

    buffer[: reader._index] = b""


@contextlib.contextmanager
def byte_reader(buffer: bytes) -> Iterator[Reader]:
    reader = Reader(buffer)

    try:
        yield reader
    finally:
        reader.close()
