from collections import deque
from doctest import UnexpectedException
from email.generator import Generator
from logging import getLogger
from socket import socket
from typing import Any, Callable
import errno
import json
from socket_frame.constants import HeaderTypeEnum

from socket_frame.message_create import make_message

from .header import get_message_length_from_header
from .settings import TcpSettings
from .exceptions import OnMessageEffectNotSet, UnexpectedSocketError, SocketNotReadyYetTryAgainException


logger = getLogger(__name__)


class Worker():
    '''
    worker for a blocking socket
    executes sending message for client and lets handler interact with message by injecting its effect as self._on_message
    '''
    def __init__(self, connection: socket, settings: TcpSettings):
        self.conn = connection

        self.settings = settings
        self._on_message = None
        self._on_connect = None
        self._received_buffer = deque([])

    def send_message(self, msg):
        '''method which can be called only by related handler'''
        length_sent = 0
        message_to_send = make_message(msg, self.settings)
        logger.debug('sending message %s', message_to_send)
        while length_sent < len(message_to_send):
            length_sent += self.conn.send(message_to_send[length_sent:])
    
    def on_connect(self):
        if self._on_connect is None:
            pass
        else:
            self.on_connect()

    def on_message(self, msg):
        if self._on_message is None:
            raise OnMessageEffectNotSet
        else:
            self._on_message(msg)

    def set_on_connect(self, effect_from_handler: Callable) -> None:
        self._on_connect = effect_from_handler

    def set_on_message(self, effect_from_handler: Callable) -> None:
        self._on_message = effect_from_handler

    def disconnect(self):
        #self.conn.send(self.settings.DISCONNECT_MESSAGE)
        self.conn.shutdown(1)
        self.conn.close()
    
    def run(self):
        self.on_connect()

        while True:
            msg = self.get_next_message()
            self.on_message(msg)
    
    def get_next_message(self):
        if self.settings.HEADER_TYPE is HeaderTypeEnum.FIXED_LENGTH:
            header = self._receive_defined_length(self, self.settings.HEADER_LENGTH)
        elif self.settings.HEADER_TYPE is HeaderTypeEnum.DELIMITER_TERMINATED:
            header = self._receive_until_termination_sequence()
        else:
            raise NotImplementedError
        logger.debug('got header: %s', header)
        msg_length = get_message_length_from_header(header, settings=self.settings)
        logger.debug('got msg_len: %s', msg_length)
        msg =self._receive_defined_length(msg_length)
        logger.debug('got msg: %s', msg)
        message_parsed = json.loads(msg.decode())
        return message_parsed
    
    def _receive_defined_length(self, length: int):
        collected = b''
        while len(collected) < length:
            if self._received_buffer:
                collected += self._received_buffer.popleft()
            else:
                collected += self.conn.recv(length - len(collected))
        
        if len(collected) > length:
            if self._received_buffer:
                # if buffer still contains chunks of next msgs, e.g. this part was from buffer
                self._received_buffer.appendleft(collected[length:])
            else:
                self._received_buffer.append(collected[length:])
        return collected
    
    def _receive_until_termination_sequence(self):
        collected = b''
        termination_sequence_bytes = self.settings.HEADER_TERMINATION_SEQUENCE.encode(self.settings.MSG_FORMAT)
        while termination_sequence_bytes not in collected:
            if self._received_buffer:
                collected += self._received_buffer.popleft()
            else:
                collected += self.conn.recv(self.settings.BYTES_CHUNK_SIZE)
        
        # we cannot be sure how many messages we have received (e.g. for ws-like we could have more than one)
        required, remaining = collected.split(termination_sequence_bytes, 1)
        if remaining:
            if self._received_buffer:
                # similar logic: we could take this from buffer, not from conn
                self._received_buffer.appendleft(remaining)
            else:
                self._received_buffer.append(remaining)
        return required
