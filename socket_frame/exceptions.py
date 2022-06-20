class MessageLengthExceedsHeaderCapacity(Exception):
    pass


class OnMessageEffectNotSet(Exception):
    pass


class CoreHandlerNotSpecified(Exception):
    pass


class CallingMethodForNonConnectedClient(Exception):
    pass