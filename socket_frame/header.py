from .exceptions import MessageLengthExceedsHeaderCapacity
from .settings import TcpSettings


def make_header_bytestr(message_length: int, settings: TcpSettings) -> bytes:
    encoded_msg_length = str(message_length).encode(settings.MSG_FORMAT)
    free_space = settings.HEADER_LENGTH - message_length
    if free_space >= 0:
        header_bytestr = encoded_msg_length + b' ' * (settings.HEADER_LENGTH - len(encoded_msg_length))
    else:
        raise MessageLengthExceedsHeaderCapacity
    return header_bytestr


def get_message_length_from_header(header: bytes, settings: TcpSettings) -> int:
    header_str = header.decode(settings.MSG_FORMAT)
    msg_length = int(header_str)
    return msg_length
