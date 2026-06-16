import serial.tools.list_ports  # type: ignore

from dataclasses import dataclass
from enum import IntEnum
import threading
import hashlib
import queue
import time
import os

from const import ERROR

@dataclass
class COMPort:
    name: str
    port: str

class COM:
    def __init__(self) -> None:
        self.conn_port = None
        self._user_timeout: float | None = None
        self._reader_thread: threading.Thread | None = None
        self._reader_active = False
        self._pong_event = threading.Event()
        self._pong_time: float | None = None
        self._ping_sent_time: float | None = None
        self._expected_token: str = ""
        self.read_queue: queue.Queue[bytes] = queue.Queue()

    def get_all_devices(self) -> list[COMPort]:
        ports: list[COMPort] = []
        all_ports = serial.tools.list_ports.comports()
        for port in all_ports:
            if port.vid is not None or "Virtual" in port.description:
                ports.append(COMPort(port.description, port.device))
        return ports

    def connect(self,
                COMPort: COMPort,
                baudrate=9600,
                bytesize=8,
                parity="N",
                stopbits=1,
                timeout=None,
                xonxoff=False,
                rtscts=False,
                write_timeout=None,
                dsrdtr=False,
                inter_byte_timeout=None,
                exclusive=None
    ):
        self._user_timeout = timeout
        self.conn_port = serial.Serial(
            port=COMPort.port,
            baudrate=baudrate,
            bytesize=bytesize,
            parity=parity,
            stopbits=stopbits,
            timeout=0.1,
            xonxoff=xonxoff,
            rtscts=rtscts,
            write_timeout=write_timeout,
            dsrdtr=dsrdtr,
            inter_byte_timeout=inter_byte_timeout,
            exclusive=exclusive
        )
        self._start_reader()

    def disconnect(self) -> None:
        self._stop_reader()
        if self.conn_port and self.conn_port.is_open:
            self.conn_port.close()
            self.conn_port = None

    def _start_reader(self):
        self._reader_active = True
        self._reader_thread = threading.Thread(target=self._reader_loop, daemon=True)
        self._reader_thread.start()

    def _stop_reader(self):
        self._reader_active = False

    def _reader_loop(self):
        while self._reader_active:
            try:
                if not self.conn_port or not self.conn_port.is_open:
                    time.sleep(0.05)
                    continue
                line = self.conn_port.readline()
                if not line:
                    time.sleep(0.05)
                    continue
                decoded = line.decode('utf-8', errors='ignore').strip()
                if decoded.startswith("PING:") and len(decoded) == 13:
                    token = decoded[5:]
                    self.conn_port.write(f"PONG:{token}\n".encode('utf-8'))
                elif decoded.startswith("PONG:") and len(decoded) == 13:
                    if self._ping_sent_time is not None and decoded[5:] == self._expected_token:
                        self._pong_time = (time.perf_counter() - self._ping_sent_time) * 1000
                        self._pong_event.set()
                else:
                    self.read_queue.put(line)
            except Exception:
                time.sleep(0.05)

    def write(self, message: str) -> bool:
        if not self.conn_port or not self.conn_port.is_open:
            return False
        return bool(self.conn_port.write(message.encode('utf-8')))

    def read(self) -> bytes | None:
        chunks = []
        try:
            while True:
                chunks.append(self.read_queue.get_nowait())
        except queue.Empty:
            pass
        return b"".join(chunks) if chunks else None

    def ping(self) -> float | ERROR:
        if not self.conn_port or not self.conn_port.is_open:
            return ERROR.NO_CONNECTION
        print("Pinging")
        self._pong_event.clear()
        self._pong_time = None
        self._expected_token = self._make_ping_token()
        self._ping_sent_time = time.perf_counter()
        self.conn_port.write(f"PING:{self._expected_token}\n".encode('utf-8'))
        if self._pong_event.wait(timeout=1.0):
            return self._pong_time if self._pong_time is not None else ERROR.CONNECTION_TIMEOUT
        return ERROR.CONNECTION_FAILURE

    def _make_ping_token(self) -> str:
        return hashlib.sha1(os.urandom(8)).hexdigest()[:8]
