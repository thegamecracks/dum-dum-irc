from enum import Enum


class ClientMessageType(Enum):
    AUTHENTICATE = 0
    SEND_MESSAGE = 1


class ServerMessageType(Enum):
    INCOMPATIBLE_VERSION = 0
    ACKNOWLEDGE_AUTHENTICATION = 1
