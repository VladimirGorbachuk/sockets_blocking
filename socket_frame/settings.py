import os
import socket
from socket import gethostbyname, gethostname
from typing import Optional

from .constants import HeaderTypeEnum

class TcpSettings():
    HEADER_LENGTH: int
    PORT: int
    MSG_FORMAT: str
    DISCONNECT_MESSAGE: str
    SERVER_ADDRESS: str
    MSGS_ARE_FIXED_LENGTH_BOOL: bool
    MSG_LENGTH_FIXED: Optional[int]
    THREADPOOL_SIZE: int
    BYTES_CHUNK_SIZE: int
    SOCKET_TIMEOUT: float
    BLOCKING_MODE: bool
    HEADER_TYPE: HeaderTypeEnum
    HEADER_TERMINATION_SEQUENCE: str

    def __init__(
        self,
        *,
        header_length: int = 64,
        port: int = 5050,
        msg_format: str = 'utf-8',
        disconnect_message: str = '!DISCONNECT',
        server_address: str = None,
        msgs_are_fixed_length_bool: bool = False,
        msgs_length_fixed: Optional[int] = None,
        threadpool_size: int = 10,
        bytes_chunk_size: int = 4096,
        socket_timeout: float = 5,
        blocking_mode: bool = True,
        header_type: HeaderTypeEnum = HeaderTypeEnum.DELIMITER_TERMINATED,
        header_termination_sequence: str = '\r\n\r\n'
    ):
        self.HEADER_LENGTH = header_length
        self.PORT = port
        self.MSG_FORMAT = msg_format
        self.DISCONNECT_MESSAGE = disconnect_message
        if server_address is None:
            self.SERVER_ADDRESS = gethostbyname(gethostname())
        else:
            self.SERVER_ADDRESS = server_address
        self.MSGS_ARE_FIXED_LENGTH_BOOL = msgs_are_fixed_length_bool
        if msgs_length_fixed:
            self.MSG_LENGTH_FIXED = msgs_length_fixed
        else:
            self.MSG_LENGTH_FIXED = None
        self.THREADPOOL_SIZE = threadpool_size
        self.BYTES_CHUNK_SIZE = bytes_chunk_size
        self.SOCKET_TIMEOUT = socket_timeout
        self.BLOCKING_MODE_BOOL = blocking_mode
        self.HEADER_TYPE = header_type
        self.HEADER_TERMINATION_SEQUENCE = header_termination_sequence
    
    @classmethod
    def initialize_from_env_vars(cls):
        header_length = int(os.environ.get('HEADER_LENGTH', 64))
        port = int(os.environ.get('PORT', 5050)) # no need for that
        msg_format = os.environ.get('FORMAT', 'utf-8')
        disconnect_message = os.environ.get('DISCONNECT_MESSAGE','!DISCONNECT')
        server_address = os.environ.get('SERVER_ADDRESS', gethostbyname(gethostname()))
        msgs_are_fixed_length_bool = os.environ.get('MSGS_ARE_FIXED_LENGTH_BOOL', False) == 'True'
        if os.environ.get('MSG_LENGTH_FIXED'):
            msg_length_fixed = int(os.environ['MSG_LENGTH_FIXED'])
        else:
            msg_length_fixed = None
        thread_pool_size = os.environ.get('THREADPOOL_SIZE', 10)
        bytes_chunk_size = os.environ.get('BYTES_CHUNK_SIZE', 4096)
        socket_timeout = os.environ.get('SOCKET_TIMEOUT', 4096)
        blocking_mode = os.environ.get('BLOCKING_MODE_BOOL') == 'True'
        header_type = os.environ.get('HEADER_TYPE', HeaderTypeEnum.DELIMITER_TERMINATED.value)
        header_termination_sequence = os.environ.get('HEADER_TERMINATION_SEQUENCE', '\r\n\r\n')

        return cls(
            header_length=header_length,
            port=port,
            msg_format=msg_format,
            disconnect_message=disconnect_message,
            server_address=server_address,
            msgs_are_fixed_length_bool=msgs_are_fixed_length_bool,
            msg_length_fixed=msg_length_fixed,
            thread_pool_size=thread_pool_size,
            bytes_chunk_size=bytes_chunk_size,
            socket_timeout=socket_timeout,
            blocking_mode=blocking_mode,
            header_type=header_type,
            header_termination_sequence=header_termination_sequence,
        )