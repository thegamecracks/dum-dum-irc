import bisect
import collections
from typing import Sequence, TypeAlias

from .protocol.channel import Channel
from .protocol.message import Message

User: TypeAlias = str


class HighCommand:
    def __init__(self) -> None:
        self._channels: dict[str, Channel] = {}
        self._messages: dict[str, list[Message]] = collections.defaultdict(list)
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

    def get_messages(
        self,
        channel_name: str,
        *,
        before: int | None = None,
        after: int | None = None,
    ) -> Sequence[Message]:
        messages = self._messages[channel_name]

        if before is not None:
            i = bisect.bisect_left(messages, before, key=lambda m: m.id)
            messages = messages[i:]

        if after is not None:
            i = bisect.bisect_right(messages, after, key=lambda m: m.id)
            messages = messages[:i]

        return messages[-100:]

    def add_message(self, message: Message) -> None:
        messages = self._messages[message.channel_name]
        bisect.insort(messages, message, key=lambda m: m.id)

    def get_message(self, channel_name: str, id: int) -> Message | None:
        messages = self._messages[channel_name]
        if len(messages) < 1:
            return None

        i = self._index_message(messages, id)
        message = messages[i]
        if message.id == id:
            return message

    def remove_message(self, channel_name: str, id: int) -> Message | None:
        messages = self._messages[channel_name]
        if len(messages) < 1:
            return None

        i = self._index_message(messages, id)
        message = messages[i]
        if message.id == id:
            del messages[i]
            return message

    def _index_message(self, messages: Sequence[Message], id: int) -> int:
        return bisect.bisect_left(messages, id, key=lambda m: m.id)

    @property
    def users(self) -> tuple[User, ...]:
        return tuple(self._users.values())

    def add_user(self, user: User) -> None:
        self._users[user] = user

    def get_user(self, nick: str) -> User | None:
        return self._users.get(nick)

    def remove_user(self, nick: str) -> User | None:
        return self._users.pop(nick, None)
