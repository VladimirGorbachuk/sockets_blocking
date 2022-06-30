from logging import getLogger
from multiprocessing.pool import ThreadPool
import socket

from .exceptions import CoreHandlerNotSpecified
from .settings import TcpSettings
from .worker import Worker


logger = getLogger(__name__)


class Server():
    def __init__(self, settings: TcpSettings, core_handler=None):
        self.workers_pool = ThreadPool(settings.THREADPOOL_SIZE)
        self.settings = settings
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.settimeout(self.settings.SOCKET_TIMEOUT)
        self.server.bind((settings.SERVER_ADDRESS, settings.PORT))
        if core_handler:
            self.default_handler = core_handler
        else:
            raise CoreHandlerNotSpecified
    
    def run(self):
        try:
            self.server.listen()
            logger.debug("[LISTENING] Server is listening on %s", self.settings.SERVER_ADDRESS)
            while True:
                conn, addr = self.server.accept()
                logger.info('listening to a new client')
                worker = Worker(conn, settings=self.settings)
                self.workers_pool.apply_async(func=self.default_handler, args=(worker,), kwds={'settings': self.settings})
        except Exception as e:
            logger.exception('an unexpected ServerError has occured %s', e)
        finally:
            self.server.shutdown(1)
            self.server.close()
