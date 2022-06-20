from logging import basicConfig, DEBUG, getLogger

from socket_frame.client import Client
from socket_frame.settings import TcpSettings


basicConfig()
logger = getLogger(__name__)
logger.setLevel(DEBUG)

if __name__ == '__main__':
    settings = TcpSettings()
    client = Client(settings=settings)
    with client.connect() as connected_client:
        connected_client.send('whatever')
        response = connected_client.receive_one_msg()
        logger.info(response)
        connected_client.send('another message')
        response_2 = connected_client.receive_one_msg()
        logger.info(response_2)

