from typing import Sequence, Type, TypeVar

import pytest

from dumdum.protocol import (
    Channel,
    Client,
    ClientEventAuthentication,
    ClientEventChannelsListed,
    ClientEventIncompatibleVersion,
    ClientEventMessagesListed,
    ClientState,
    InvalidStateError,
    MalformedDataError,
    Message,
    Protocol,
    Server,
    ServerEventAuthentication,
    ServerEventIncompatibleVersion,
    ServerEventListChannels,
    ServerEventListMessages,
    ServerEventMessageReceived,
    ServerState,
)

T = TypeVar("T")


def communicate(
    sender: Protocol,
    data: bytes,
    receiver: Protocol,
) -> tuple[list[object], list[object]]:
    def send_loop():
        i, outgoing = 0, data
        while len(outgoing) > 0:
            receiver, receiver_events = order[i % len(order)]
            print(f"{type(receiver).__name__} << {outgoing}")
            events, outgoing = receiver.receive_bytes(outgoing)
            receiver_events.extend(events)
            i += 1

    sender_events: list[object] = []
    receiver_events: list[object] = []
    order = [(receiver, receiver_events), (sender, sender_events)]
    send_loop()
    return sender_events, receiver_events


def assert_event_order(events: Sequence[object], *expected_events: Type[object]):
    # fmt: off
    assert len(events) == len(expected_events), \
        "Expected exactly {} event(s), got {} instead".format(
        len(expected_events),
        len(events),
    )

    for i, (event, type_) in enumerate(zip(events, expected_events)):
        assert isinstance(event, type_), \
            "Expected {} at index {}, got {} instead".format(
            type_.__name__,
            i,
            type(event).__name__,
        )
    # fmt: on


def test_authenticate():
    nick = "thegamecracks"
    client = Client(nick=nick)
    server = Server()

    client_events, server_events = communicate(client, client.authenticate(), server)
    assert client_events == []
    assert server_events == [ServerEventAuthentication(nick=nick)]

    data = server.acknowledge_authentication(success=True)
    server_events, client_events = communicate(server, data, client)
    assert client_events == [ClientEventAuthentication(success=True)]
    assert server_events == []


def test_authenticate_incompatible_version():
    nick = "thegamecracks"
    client = Client(nick=nick)
    server = Server()

    client.PROTOCOL_VERSION = server.PROTOCOL_VERSION + 1  # type: ignore
    if client.PROTOCOL_VERSION > 255:
        client.PROTOCOL_VERSION = server.PROTOCOL_VERSION - 1  # type: ignore

    assert client.PROTOCOL_VERSION != server.PROTOCOL_VERSION

    client_events, server_events = communicate(client, client.authenticate(), server)
    assert client_events == [
        ClientEventIncompatibleVersion(
            client_version=client.PROTOCOL_VERSION,
            server_version=server.PROTOCOL_VERSION,
        )
    ]
    assert server_events == [
        ServerEventIncompatibleVersion(
            version=client.PROTOCOL_VERSION,
        )
    ]


def test_send_message():
    nick = "thegamecracks"
    content = "Hello world!"
    channel_name = "general"

    client = Client(nick=nick)
    server = Server()

    communicate(client, client.authenticate(), server)
    communicate(server, server.acknowledge_authentication(success=True), client)

    client_events, server_events = communicate(
        client,
        client.send_message(channel_name, content),
        server,
    )
    assert client_events == []
    assert server_events == [ServerEventMessageReceived(channel_name, content)]


def test_list_channels():
    channels = [
        Channel("announcements"),
        Channel("general"),
        Channel("memes"),
        Channel("coding-lounge"),
        Channel("fishing-trips"),
    ]

    client = Client(nick="thegamecracks")
    server = Server()

    communicate(client, client.authenticate(), server)
    communicate(server, server.acknowledge_authentication(success=True), client)

    client_events, server_events = communicate(client, client.list_channels(), server)
    assert client_events == []
    assert server_events == [ServerEventListChannels()]

    data = server.list_channels(channels)
    server_events, client_events = communicate(server, data, client)
    assert client_events == [ClientEventChannelsListed(channels)]
    assert server_events == []


def test_unauthenticated_send_message():
    nick = "thegamecracks"
    content = "Hello world!"
    channel = Channel("general")

    client = Client(nick=nick)
    server = Server()

    with pytest.raises(InvalidStateError):
        client.send_message(channel.name, content)

    client._state = ClientState.READY
    data = client.send_message(channel.name, content)

    with pytest.raises(InvalidStateError):
        communicate(client, data, server)


def test_unauthenticated_server_send_message():
    nick = "thegamecracks"
    content = "Hello world!"
    message = Message(0, "general", nick, content)

    client = Client(nick=nick)
    server = Server()

    with pytest.raises(InvalidStateError):
        server.send_message(message)

    server._state = ServerState.READY
    data = server.send_message(message)

    with pytest.raises(InvalidStateError):
        communicate(server, data, client)


def test_list_messages():
    nick = "thegamecracks"
    channel = Channel("general")

    client = Client(nick=nick)
    server = Server()

    communicate(client, client.authenticate(), server)
    communicate(server, server.acknowledge_authentication(success=True), client)

    before = 1
    after = 2
    data = client.list_messages(channel.name, before=before, after=after)
    client_events, server_events = communicate(client, data, server)
    assert client_events == []
    assert server_events == [ServerEventListMessages(channel.name, before, after)]

    messages = [Message(i, channel.name, nick, "Hello world!") for i in range(100)]
    data = server.list_messages(messages)
    server_events, client_events = communicate(server, data, client)
    assert server_events == []
    assert client_events == [ClientEventMessagesListed(messages)]


def test_invalid_message_type():
    client = Client("thegamecracks")
    server = Server()

    with pytest.raises(MalformedDataError):
        client.receive_bytes(b"\xff")

    with pytest.raises(MalformedDataError):
        server.receive_bytes(b"\xff")
