from __future__ import annotations

import bisect
import collections
from typing import Sequence, TypeAlias

from dumdum.protocol import Channel, Message

User: TypeAlias = str


class ServerState:
    def __init__(self, *, message_cache: MessageCache) -> None:
        self.message_cache = message_cache
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

    def get_messages(
        self,
        channel_name: str,
        *,
        before: int | None = None,
        after: int | None = None,
        limit: int = 100,
    ) -> Sequence[Message]:
        return self.message_cache.get_messages(
            channel_name,
            before=before,
            after=after,
            limit=limit,
        )

    def add_message(self, message: Message) -> None:
        return self.message_cache.add_message(message)

    def get_message(self, channel_name: str, id: int) -> Message | None:
        return self.message_cache.get_message(channel_name, id)

    def remove_message(self, channel_name: str, id: int) -> Message | None:
        return self.message_cache.remove_message(channel_name, id)

    @property
    def users(self) -> tuple[User, ...]:
        return tuple(self._users.values())

    def add_user(self, user: User) -> None:
        self._users[user] = user

    def get_user(self, nick: str) -> User | None:
        return self._users.get(nick)

    def remove_user(self, nick: str) -> User | None:
        return self._users.pop(nick, None)


class MessageCache:
    _channel_messages: dict[str, collections.deque[Message]]

    def __init__(self, *, max_messages: int) -> None:
        self.max_messages = max_messages
        self._channel_messages = collections.defaultdict(self._create_message_queue)

    def add_message(self, message: Message) -> None:
        messages = self._channel_messages[message.channel_name]

        # Ensure deque isn't full before insorting it
        messages.append(message)
        assert messages.pop() == message

        bisect.insort(messages, message, key=lambda m: m.id)

    def get_message(self, channel_name: str, id: int) -> Message | None:
        messages = self._channel_messages[channel_name]
        if len(messages) < 1:
            return None

        i = self._index_message(messages, id)
        message = messages[i]
        if message.id == id:
            return message

    def get_messages(
        self,
        channel_name: str,
        *,
        before: int | None = None,
        after: int | None = None,
        limit: int = 100,
    ) -> Sequence[Message]:
        messages = list(self._channel_messages[channel_name])

        if before is not None:
            i = bisect.bisect_left(messages, before, key=lambda m: m.id)
            messages = messages[i:]

        if after is not None:
            i = bisect.bisect_right(messages, after, key=lambda m: m.id)
            messages = messages[:i]

        return messages[-limit:]

    def remove_message(self, channel_name: str, id: int) -> Message | None:
        messages = self._channel_messages[channel_name]
        if len(messages) < 1:
            return None

        i = self._index_message(messages, id)
        message = messages[i]
        if message.id == id:
            del messages[i]
            return message

    def _create_message_queue(self) -> collections.deque[Message]:
        return collections.deque(maxlen=self.max_messages)

    def _index_message(self, messages: Sequence[Message], id: int) -> int:
        return bisect.bisect_left(messages, id, key=lambda m: m.id)
