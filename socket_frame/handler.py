from functools import partial
from logging import getLogger
from typing import Any, Generator, Type

from .worker import Worker
from .settings import TcpSettings


logger = getLogger(__name__)


class BaseHandler():
    '''
    Class to handle message, instance interacts only with related worker by using its' send/receive methods
    '''
    def __init__(self, worker: Worker, settings: TcpSettings):
        self.worker = worker
        self.worker.set_on_message(lambda msg: self.handle_message(msg))
        self.settings = settings  # currently not used

    def handle_message(self, msg: Any):
        raise NotImplementedError
    

class EchoHandler(BaseHandler):
    '''
    Class which just returns message back to sender
    '''
    def handle_message(self, msg: Any):
        logger.info('got message %s in handler', msg)
        self.worker.send_message(msg)


class EchoAsyncHandler(BaseHandler):
    '''
    Class which just returns message back to sender
    '''
    def handle_message(self, msg: Any):
        logger.info('got message %s in handler', msg)
        yield from self.worker.send_message(msg)


def run_handler(worker: Worker, *, handler_cls: Type[BaseHandler], settings: TcpSettings):
    handler_cls(worker, settings)
    logger.info('handler has been bound')
    worker.run()

def run_handler(worker: Worker, *, handler_cls: Type[BaseHandler], settings: TcpSettings) -> Generator:
    handler_cls(worker, settings)
    logger.info('handler has been bound')
    return worker.run()


run_echo = partial(run_handler, handler_cls=EchoHandler)

run_echo_async = partial(run_handler, handler_cls=EchoAsyncHandler)