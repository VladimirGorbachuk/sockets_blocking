from logging import getLogger
from multiprocessing.pool import ThreadPool
from queue import Queue
from threading import Thread
from time import sleep
import errno
import queue
import select
import socket

from .constants import STOP_DAEMON_THREAD_EVENT_LOOP_TASK_STR
from .exceptions import CoreHandlerNotSpecified, SocketIsClosed, UnexpectedSocketError
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
            logger.debug("Server is listening on %s", self.settings.SERVER_ADDRESS)
            while True:
                conn, addr = self.server.accept()
                logger.debug('Listening to a new client')
                worker = Worker(conn, settings=self.settings)
                self.workers_pool.apply_async(func=self.default_handler, args=(worker,), kwds={'settings': self.settings})
        except Exception as e:
            logger.exception('an unexpected ServerError has occured %s', e)
        finally:
            self.server.shutdown(socket.SHUT_RDWR)
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
    
    def run(self):
        try:
            self._run_separate_thread_as_event_loop()
            self._run()
        finally:
            self.server.shutdown(socket.SHUT_RDWR)
            self.server.close()
            self.active_tasks_queue.put(STOP_DAEMON_THREAD_EVENT_LOOP_TASK_STR)
            self.daemon_thread.join()
    
    def _run(self):
        self.server.listen()
        while True:
            conn = None
            try:
                conn, addr = self.server.accept()
                worker = GeneratorWorker(conn, settings = self.settings)
                task = self.default_handler(worker, settings = self.settings) 
                self.active_tasks_queue.put(task)
            except socket.timeout:
                if conn:
                    conn.shutdown(socket.SHUT_RDWR)
                    conn.close()
            except socket.error as e:
                if e.args[0] in [errno.EWOULDBLOCK, errno.EAGAIN]:
                    pass
                else:
                    #FIXME: not sure it is okay to ignore any socket error, at least need to keep logs
                    logger.exception(e, stack_info=True)

    def _run_separate_thread_as_event_loop(self):
        # FIXME: possibly need to call as a daemon thread (not sure of it yet)
        self.daemon_thread.start()
    
    def _execute_event_loop_for_all_connections(self):

        while True:
            try:
                alive_task = self.active_tasks_queue.get(block=False)
                if alive_task == STOP_DAEMON_THREAD_EVENT_LOOP_TASK_STR:
                    break
            except queue.Empty:
                # FIXME: not sure what would be appropriate as a sleep value
                sleep(0)
                continue
            try:
                next(alive_task)
                self.active_tasks_queue.put(alive_task)
            except SocketIsClosed:
                # task is finished/dead - no need to keep it in event loop
                logger.info('task finished, socket is closed now')

            # FIXME: not sure that it is correct to put zero sleep here need to ask is it set as env var or zero?
            sleep(0)


class SelectBasedServer(NonBlockingSocketServer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._conn_fileno_mapped_to_tasks = {}

    def _run(self):
        self.server.listen()

        conn = None
        readable_socket_list = [self.server]
        writable_socket_list = []
        while True:
            # Get the list sockets which are readable
            if not readable_socket_list:
                readable_socket_list.append(self.server)
            readable_socket_list, writeable_socket_list, error_sockets = select.select(
                readable_socket_list, writable_socket_list, [])

            new_writable_socket_list = []
            for socket in readable_socket_list + writeable_socket_list:
                if socket is self.server:
                    conn, addr = socket.accept()
                    new_writable_socket_list.append(conn)
                else:
                    conn = socket
            
                if conn.fileno() not in self._conn_fileno_mapped_to_tasks:
                    worker = GeneratorWorker(conn, settings = self.settings)
                    task = self.default_handler(worker, settings = self.settings)
                    self._conn_fileno_mapped_to_tasks[conn.fileno()] = task
                else:
                    task = self._conn_fileno_mapped_to_tasks[conn.fileno()]
                self.active_tasks_queue.put(task)
            writable_socket_list = new_writable_socket_list
            for conn in error_sockets:
                try:
                    self._conn_fileno_mapped_to_tasks.pop(conn.fileno())
                except KeyError:
                    pass

    def _execute_event_loop_for_all_connections(self):
        while True:
            try:
                alive_task = self.active_tasks_queue.get(block=False)
                if alive_task == STOP_DAEMON_THREAD_EVENT_LOOP_TASK_STR:
                    break
            except queue.Empty:
                # FIXME: not sure what would be appropriate as a sleep value
                sleep(0)
                continue
            try:
                next(alive_task)
            except SocketIsClosed:
                # task is finished/dead - no need to keep it in event loop
                logger.info('task finished, socket is closed now')

            # FIXME: not sure that it is correct to put zero sleep here need to ask is it set as env var or zero?
            sleep(0)