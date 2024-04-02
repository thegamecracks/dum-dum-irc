from enum import Enum


class ProtocolError(Exception):
    """The base class for errors related to the protocol."""


class BufferOverflowError(ProtocolError):
    """The protocol received more data than the buffer could store.

    This may be the result of the buffer size being set too low,
    or possibly malformed data that the protocol is unable to parse.

    Clients and servers, upon receiving this error, should immediately
    terminate their connection.

    """

    def __init__(self, limit: int, len_buffer: int, len_data: int) -> None:
        super().__init__(f"Buffer limit cannot be exceeded ({limit:,d} bytes)")
        self.limit = limit
        self.len_buffer = len_buffer
        self.len_data = len_data


class MalformedDataError(ProtocolError):
    """Raised when there is unambiguously malformed data.

    Clients and servers, upon receiving this error, should immediately
    terminate their connection.

    """


class InvalidLengthError(MalformedDataError):
    """An invalid length was specified for a variable-length message."""

    def __init__(self, length: int, max_length: int) -> None:
        super().__init__(
            f"Expected message length up to {max_length}, got {length} instead"
        )
        self.length = length
        self.max_length = max_length


class InvalidStateError(ProtocolError):
    """Some action cannot be handled in the protocol's current state."""

    def __init__(self, current_state: Enum, expected_states: tuple[Enum, ...]) -> None:
        super().__init__(
            "{} must be {}, but is currently {}".format(
                type(current_state).__name__,
                " or ".join(s.name for s in expected_states),
                current_state.name,
            )
        )
        self.current_state = current_state
        self.expected_states = expected_states
