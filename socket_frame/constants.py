from enum import Enum


class HeaderTypeEnum(Enum):
    FIXED_LENGTH = 'fixed_length'
    DELIMITER_TERMINATED = 'delimiter_terminated'


class MessagePartsEnum(Enum):
    HEADER = 'header'
    PAYLOAD = 'payload'


class CurrentOperationEnum(Enum):
    NO_OPERATION = 'no_operation'
    WRITING = 'writing'
    READING = 'reading'


STOP_DAEMON_THREAD_EVENT_LOOP_TASK_STR = 'STOP'