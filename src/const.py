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

class MODBUS_MODE(StrEnum):
    MASTER = "Master"
    SLAVE = "Slave"

class MODBUS_CMD(IntEnum):
    WRITE_TEXT = 1
    READ_TEXT = 2

class MODBUS_LIMIT(IntEnum):
    BROADCAST_ADDRESS = 0
    MIN_SLAVE_ADDRESS = 1
    MAX_SLAVE_ADDRESS = 247
    MIN_RETRIES = 0
    MAX_RETRIES = 5

class MODBUS_ERROR(IntEnum):
    NO_CONNECTION = -1
    TRANSACTION_TIMEOUT = -2
    INVALID_LRC = -3
    NO_RESPONSE = -4
    EXCEPTION_RESPONSE = -5

class MODBUS_EXCEPTION(IntEnum):
    ILLEGAL_FUNCTION = 1
    ILLEGAL_DATA_ADDRESS = 2
    ILLEGAL_DATA_VALUE = 3
    SLAVE_DEVICE_FAILURE = 4

class MODBUS_FRAME(StrEnum):
    START = ":"
    END = "\r\n"

class MODBUS_MESSAGE(StrEnum):
    NO_CONNECTION = "No Connection"
    TRANSACTION_TIMEOUT = "Transaction Timed Out"
    INVALID_LRC = "Invalid Checksum (LRC)"
    NO_RESPONSE = "No Response From Slave"
    EXCEPTION_RESPONSE = "Exception Response Received"
    BROADCAST_SENT = "Broadcast Sent"
    TRANSACTION_SUCCESS = "Transaction Successful"
    SLAVE_LISTENING = "Slave Listening"
    SLAVE_STOPPED = "Slave Stopped"
    INVALID_ADDRESS = "Invalid Slave Address"
    TEXT_WRITTEN = "Text Written To Slave"
    TEXT_READ = "Text Read From Slave"

class COLOR(StrEnum):
    BACKGROUND =  "#2d2926"
    ACCENT_1 =    "#7c878e"
    ACCENT_2 =    "#003da5"
    TEXT_MAIN =   "#f1be48"
    TEXT_FADE =   "#efbe7d"
    TRANSPARENT = "#000001"
