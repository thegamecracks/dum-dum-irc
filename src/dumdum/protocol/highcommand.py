from typing import TypeAlias

from .channel import Channel

User: TypeAlias = str


class HighCommand:
    def __init__(self) -> None:
        self._channels: dict[str, Channel] = {}
        self._users: dict[str, User] = {}

    @property
    def channels(self) -> tuple[Channel, ...]:
        return tuple(self._channels.values())

    def add_channel(self, channel: Channel) -> None:
        self._channels[channel.name] = channel

    def get_channel(self, name: str) -> Channel | None:
        return self._channels.get(name)

    def remove_channel(self, name: str) -> Channel | None:
        return self._channels.pop(name, None)

    @property
    def users(self) -> tuple[User, ...]:
        return tuple(self._users.values())

    def add_user(self, user: User) -> None:
        self._users[user] = user

    def get_user(self, nick: str) -> User | None:
        return self._users.get(nick)

    def remove_user(self, nick: str) -> User | None:
        return self._users.pop(nick, None)
