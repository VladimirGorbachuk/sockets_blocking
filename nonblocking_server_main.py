from logging import basicConfig, getLogger, INFO

from socket_frame.handler import run_echo_async
from socket_frame.server import NonBlockingSocketServer
from socket_frame.settings import TcpSettings


basicConfig()
logger = getLogger(__name__)
logger.setLevel(INFO)


if __name__ == '__main__':
    settings = TcpSettings()
    server = NonBlockingSocketServer(settings, core_handler=run_echo_async)
    server.run()
