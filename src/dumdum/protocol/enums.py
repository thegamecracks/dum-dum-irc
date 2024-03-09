from enum import Enum


class ClientMessageType(Enum):
    AUTHENTICATE = 0
    SEND_MESSAGE = 1
    LIST_CHANNELS = 2


class ServerMessageType(Enum):
    INCOMPATIBLE_VERSION = 0
    ACKNOWLEDGE_AUTHENTICATION = 1
    SEND_MESSAGE = 2
    LIST_CHANNELS = 3
