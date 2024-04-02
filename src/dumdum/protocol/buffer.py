from .errors import BufferOverflowError


def extend_limited_buffer(
    buffer: bytearray,
    data: bytes | bytearray,
    *,
    limit: int | None,
) -> None:
    if limit is None:
        buffer.extend(data)
        return

    len_buffer, len_data = len(buffer), len(data)
    if len_buffer + len_data > limit:
        raise BufferOverflowError(limit, len_buffer, len_data)

    buffer.extend(data)
