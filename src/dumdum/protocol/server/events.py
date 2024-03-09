from dataclasses import dataclass

from dumdum.protocol.channel import Channel


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

    success: bool
    nick: str


@dataclass
class ServerEventMessageReceived(ServerEvent):
    """The client sent a message to the server."""

    channel: Channel
    content: str
