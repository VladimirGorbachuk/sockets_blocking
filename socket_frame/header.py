from .constants import HeaderTypeEnum
from .exceptions import MessageLengthExceedsHeaderCapacity
from .settings import TcpSettings


def make_header_bytestr_delimiter_terminated(message_length: int, settings: TcpSettings) -> bytes:
    encoded_msg_length = str(message_length).encode(settings.MSG_FORMAT)
    header_bytestr = encoded_msg_length + settings.HEADER_TERMINATION_SEQUENCE.encode(settings.MSG_FORMAT)
    return header_bytestr


def make_header_bytestr_fixed_length(message_length: int, settings: TcpSettings) -> bytes:
    encoded_msg_length = str(message_length).encode(settings.MSG_FORMAT)
    free_space = settings.HEADER_LENGTH - len(encoded_msg_length)
    if free_space >= 0:
        header_bytestr = encoded_msg_length + b' ' * free_space
    else:
        raise MessageLengthExceedsHeaderCapacity
    return header_bytestr


def make_header_bytestr(message_length: int, settings: TcpSettings) -> bytes:
    if settings.HEADER_TYPE == HeaderTypeEnum.DELIMITER_TERMINATED:
        return make_header_bytestr_delimiter_terminated(message_length, settings)
    elif settings.HEADER_TYPE == HeaderTypeEnum.FIXED_LENGTH:  # FIXME: possibly should use is
        return make_header_bytestr_fixed_length(message_length, settings)
    else:
        raise NotImplementedError


def get_message_length_from_header(header: bytes, settings: TcpSettings) -> int:
    header_str = header.decode(settings.MSG_FORMAT)
    msg_length = int(header_str)
    return msg_length
