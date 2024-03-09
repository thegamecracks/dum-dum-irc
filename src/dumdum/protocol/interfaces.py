from abc import ABC, abstractmethod
from typing import Sequence


class Protocol(ABC):
    @abstractmethod
    def receive_bytes(self, data: bytes) -> tuple[Sequence[object], bytes]:
        """Receive bytes from the sender."""
