from contextlib import contextmanager
from logging import getLogger
from typing import Any
import socket

from .exceptions import CallingMethodForNonConnectedClient
from .settings import TcpSettings
from .worker import Worker


logger = getLogger(__name__)


class Client(Worker):
    def __init__(self, *, response_handler = None, settings: TcpSettings):
        self.settings = settings
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.settimeout(self.settings.SOCKET_TIMEOUT)
        self.conn = None
        self.response_handler = response_handler
        self.worker = None
    
    @contextmanager
    def connect(self):
        try:
            self.client.connect((self.settings.SERVER_ADDRESS, self.settings.PORT))
            self.worker = Worker(self.client, settings=self.settings)
            yield self
        except ConnectionRefusedError as e:
            logger.warning('the socket server is not responding or is refusing to respond')
            raise e
        except Exception as e:
            logger.exception('unexpected error occured while connecting %s', e, stack_info = True)
        finally:
            if self.worker is not None:
                self.worker.disconnect()
            if self.conn is not None:
                self.conn.shutdown(1)
                self.conn.close()
            self.conn = None
            self.worker = None


    def send(self, msg: Any):
        if self.worker is None:
            raise CallingMethodForNonConnectedClient
        self.worker.send_message(msg)
    
    def receive_one_msg(self):
        if self.worker is None:
            raise CallingMethodForNonConnectedClient
        return self.worker.get_next_message()
        
