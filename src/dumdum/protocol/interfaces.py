from abc import ABC, abstractmethod


class Protocol(ABC):
    @abstractmethod
    def receive_bytes(self, data: bytes) -> tuple[list[object], bytes]:
        """Receive bytes from the sender."""
