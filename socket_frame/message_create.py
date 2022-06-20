import json
from typing import Any

from .header import make_header_bytestr
from .settings import TcpSettings


def make_message(payload: Any, settings: TcpSettings) -> bytes:
    payload_str = json.dumps(payload)
    payload_bytes = payload_str.encode(settings.MSG_FORMAT)
    header = make_header_bytestr(len(payload_bytes), settings)
    return header + payload_bytes
