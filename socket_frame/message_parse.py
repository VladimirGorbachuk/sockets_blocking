import json
from typing import Any

from .settings import TcpSettings

def parse_message(payload_bytes: bytes, settings: TcpSettings) -> Any:
    payload_str = payload_bytes.decode(settings.MSG_FORMAT)
    payload = json.loads(payload_str)
    return payload
    
