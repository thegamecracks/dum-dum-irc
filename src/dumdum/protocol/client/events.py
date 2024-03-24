from dataclasses import dataclass
from typing import Sequence

from dumdum.protocol.channel import Channel
from dumdum.protocol.message import Message


@dataclass
class ClientEvent:
    """An event received by the client."""


@dataclass
class ClientEventHello(ClientEvent):
    """The server responded to our hello."""

    using_ssl: bool


@dataclass
class ClientEventIncompatibleVersion(ClientEvent):
    """The server does not support our protocol version."""

    server_version: int
    client_version: int


@dataclass
class ClientEventAuthentication(ClientEvent):
    """The server responded to our authentication request."""

    success: bool


@dataclass
class ClientEventMessageReceived(ClientEvent):
    """The server broadcasted a message to the client."""

    message: Message


@dataclass
class ClientEventChannelsListed(ClientEvent):
    """The server responded to our request for a channel list."""

    channels: Sequence[Channel]


@dataclass
class ClientEventMessagesListed(ClientEvent):
    """The server responded to our request for a message list."""

    messages: Sequence[Message]
