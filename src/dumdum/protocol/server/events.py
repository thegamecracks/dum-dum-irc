from dataclasses import dataclass


@dataclass
class ServerEvent:
    """An event received by the server."""


@dataclass
class ServerEventIncompatibleVersion(ServerEvent):
    """The client tried using an incompatible protocol version."""

    version: int


@dataclass
class ServerEventAuthenticated(ServerEvent):
    """The client successfully authenticated with the server."""

    nick: str


@dataclass
class ServerEventMessageReceived(ServerEvent):
    """The client sent a message to the server."""

    content: str
