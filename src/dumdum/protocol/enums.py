from enum import Enum


class ClientMessageType(Enum):
    HELLO = 0
    AUTHENTICATE = 2
    SEND_MESSAGE = 3
    LIST_CHANNELS = 4
    LIST_MESSAGES = 5


class ServerMessageType(Enum):
    HELLO = 0
    INCOMPATIBLE_VERSION = 1
    ACKNOWLEDGE_AUTHENTICATION = 2
    SEND_MESSAGE = 3
    LIST_CHANNELS = 4
    LIST_MESSAGES = 5
