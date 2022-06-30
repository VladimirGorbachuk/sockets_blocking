import socket

class MessageLengthExceedsHeaderCapacity(Exception):
    pass


class OnMessageEffectNotSet(Exception):
    pass


class CoreHandlerNotSpecified(Exception):
    pass


class CallingMethodForNonConnectedClient(Exception):
    pass


class UnexpectedSocketError(socket.error):
    pass


class SocketNotReadyYetTryAgainException(socket.error):
    pass