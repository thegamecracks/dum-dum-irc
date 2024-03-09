from dataclasses import dataclass

from dumdum.protocol.channel import Channel


@dataclass
class ClientEvent:
    """An event received by the client."""


@dataclass
class ClientEventIncompatibleVersion(ClientEvent):
    """The server does not support our protocol version."""

    version: int


@dataclass
class ClientEventAuthentication(ClientEvent):
    """The server responded to our authentication request."""

    success: bool


@dataclass
class ClientEventMessageReceived(ClientEvent):
    """The server broadcasted a message to the client."""

    channel: Channel
    nick: str
    content: str
