from enum import IntEnum
from datetime import datetime
import os

from tools import resource_path
import atexit

class LOG_LEVEL(IntEnum):
    INFO = 1
    WARNING = 2
    ERROR = 3

class Logger:
    def __init__(self, *file: str, level: LOG_LEVEL = LOG_LEVEL.WARNING):
        self.level = level
        log_path = resource_path(*file)
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        self.log_file = open(log_path, "a")
        atexit.register(self.log_file.close)

    def log(self, log_type: LOG_LEVEL, message: str):
        if log_type < self.level:
            return
        self.log_file.write(message + "\n")
        self.log_file.flush()

    def __del__(self):
        if not self.log_file.closed:
            self.log_file.close()
