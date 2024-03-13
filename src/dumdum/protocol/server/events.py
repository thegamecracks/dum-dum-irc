from dataclasses import dataclass


@dataclass
class ServerEvent:
    """An event received by the server."""


@dataclass
class ServerEventIncompatibleVersion(ServerEvent):
    """The client tried using an incompatible protocol version."""

    version: int


@dataclass
class ServerEventAuthentication(ServerEvent):
    """The client attempted to authenticate with the server."""

    nick: str


@dataclass
class ServerEventMessageReceived(ServerEvent):
    """The client sent a message to the server."""

    channel_name: str
    content: str


@dataclass
class ServerEventListChannels(ServerEvent):
    """The client requested a list of channels."""


@dataclass
class ServerEventListMessages(ServerEvent):
    """The client requested a list of messages."""

    channel_name: str
    before: int | None
    after: int | None
