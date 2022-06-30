from enum import Enum


class HeaderTypeEnum(Enum):
    FIXED_LENGTH = 'fixed_length'
    DELIMITER_TERMINATED = 'delimiter_terminated'