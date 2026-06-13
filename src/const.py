from enum import IntEnum, StrEnum

class APP(StrEnum):
    BASE_TITLE = "COM Port Communication"
    GEOMETRY = "1160x720"

class LOG_LEVEL(IntEnum):
    INFO = 1
    WARNING = 2
    ERROR = 3

class ERROR(IntEnum):
    NO_CONNECTION = -1
    CONNECTION_FAILURE = -2
    CONNECTION_TIMEOUT = -3

class MESSAGE(StrEnum):
    NO_CONNECTION = "No Connection"
    CONNECTION_ERROR = "Connection Error"
    CONNECTION_TIMEOUT = "Connection Timed Out"
    CONNECTION_SUCCESS = "Connection Success"
    DISCONNECTION = "Disconnected"
    WRITE_SUCCESS = "Write Successful"
    WRITE_FAIL = "Write Failure"
    READ_SUCCESS = "Read Successful"
    READ_FAIL = "Read Failure"
    ERROR_UNKNOWN = "Unknown Error Occurred"
    PING_INFO = "Make sure that second device is in Listen Mode"
