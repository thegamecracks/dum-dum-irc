from dataclasses import dataclass

from dumdum.protocol.enums import ServerMessageType


@dataclass
class ServerMessageSendIncompatibleVersion:
    required: int

    def __bytes__(self) -> bytes:
        return bytes(
            [
                ServerMessageType.INCOMPATIBLE_VERSION.value,
                self.required,
            ]
        )


@dataclass
class ServerMessageAcknowledgeAuthentication:
    success: bool

    def __bytes__(self) -> bytes:
        return bytes(
            [
                ServerMessageType.ACKNOWLEDGE_AUTHENTICATION.value,
                self.success,
            ]
        )
