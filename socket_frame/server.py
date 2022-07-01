from logging import getLogger
from multiprocessing.pool import ThreadPool
from queue import Queue
from threading import Thread
from time import sleep
import errno
import queue
import socket

from .exceptions import CoreHandlerNotSpecified, UnexpectedSocketError
from .settings import TcpSettings
from .worker import Worker, GeneratorWorker


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


class NonBlockingSocketServer():
    def __init__(self, settings: TcpSettings, core_handler=None):
        self.settings = settings
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setblocking(0)
        self.server.settimeout(self.settings.SOCKET_TIMEOUT)
        self.server.bind((settings.SERVER_ADDRESS, settings.PORT))
        if core_handler:
            self.default_handler = core_handler
        else:
            raise CoreHandlerNotSpecified
        self.active_tasks_queue = Queue()
        self.daemon_thread = Thread(target = self._execute_event_loop_for_all_connections, daemon=True)
    
    def _run_separate_thread_as_event_loop(self):
        # FIXME: possibly need to call as a daemon thread (not sure of it yet)
        self.daemon_thread.start()
    
    def _execute_event_loop_for_all_connections(self):

        while True:
            try:
                print('at least maybe now we are here?')
                alive_task = self.active_tasks_queue.get(block=False)
                try:
                    print('are we even going to try?')
                    next(alive_task)
                    self.active_tasks_queue.put(alive_task)
                    print('this time we did not return it to queue?')
                except GeneratorExit:
                    print('it is finished')
                    # task is finished/dead - no need to keep it in event loop
                    logger.info('task finished')
            except queue.Empty:
                print('empty')
                sleep(2)
            # FIXME: not sure that it is correct to put zero sleep here need to ask is it set as env var or zero?
            sleep(0)
        
    
    def run(self):
        self._run_separate_thread_as_event_loop()
        self.server.listen()
        while True:
            conn = None
            try:
                conn, addr = self.server.accept()
                worker = GeneratorWorker(conn, settings = self.settings)
                task = self.default_handler(worker, settings = self.settings) 
                self.active_tasks_queue.put(task)
                print('did we put it to the queue?')
            except socket.timeout:
                if conn:
                    conn.close()
                    conn.shutdown()
            except socket.error as e:
                if e.args[0] in [errno.EWOULDBLOCK, errno.EAGAIN]:
                    pass
                else:
                    #FIXME: not sure it is okay to ignore any socket error, at least need to keep logs
                    logger.exception(e, stack_info=True)
    