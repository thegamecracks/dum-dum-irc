from dataclasses import dataclass, field

from .channel import Channel


@dataclass
class HighCommand:
    # users: dict[str, None] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self._channels: dict[str, Channel] = {}

    @property
    def channels(self) -> tuple[Channel, ...]:
        return tuple(self._channels.values())

    def add_channel(self, channel: Channel) -> None:
        self._channels[channel.name] = channel

    def get_channel(self, name: str) -> Channel | None:
        return self._channels.get(name)

    def remove_channel(self, name: str) -> Channel | None:
        return self._channels.pop(name, None)
