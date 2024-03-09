from typing import Sequence, Type, TypeVar

from dumdum.protocol import (
    Channel,
    Client,
    ClientEventAuthentication,
    ClientEventMessageReceived,
    HighCommand,
    Protocol,
    Server,
    ServerEventAuthenticated,
    ServerEventMessageReceived,
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
    hc = HighCommand()

    client = Client(nick="thegamecracks")
    server = Server(hc)

    client_events, server_events = communicate(client, client.authenticate(), server)
    assert_event_order(client_events, ClientEventAuthentication)
    assert_event_order(server_events, ServerEventAuthenticated)


def test_send_message():
    nick = "thegamecracks"
    content = "Hello world!"

    hc = HighCommand()
    channel = Channel("general")
    hc.add_channel(channel)

    client = Client(nick=nick)
    server = Server(hc)
    communicate(client, client.authenticate(), server)

    client_events, server_events = communicate(
        client,
        client.send_message(channel.name, content),
        server,
    )
    assert_event_order(client_events, ClientEventMessageReceived)
    assert_event_order(server_events, ServerEventMessageReceived)
    assert client_events[0] == ClientEventMessageReceived(channel, nick, content)
    assert server_events[0] == ServerEventMessageReceived(channel, content)
