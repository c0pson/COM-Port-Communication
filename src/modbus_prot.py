import threading
import time

from serial_com import COM
from const import (
    MODBUS_CMD,
    MODBUS_LIMIT,
    MODBUS_ERROR,
    MODBUS_EXCEPTION,
    MODBUS_FRAME,
)

class ModbusFrame:
    def __init__(self, address: int, command: int, data: bytes) -> None:
        self.address = address
        self.command = command
        self.data = data

    @staticmethod
    def lrc(payload: bytes) -> int:
        return ((~sum(payload) + 1) & 0xFF)

    def encode(self) -> bytes:
        payload = bytes([self.address, self.command]) + self.data
        checksum = ModbusFrame.lrc(payload)
        ascii_body = (payload + bytes([checksum])).hex().upper()
        return f"{MODBUS_FRAME.START}{ascii_body}{MODBUS_FRAME.END}".encode('ascii')

    @staticmethod
    def decode(raw: bytes) -> "ModbusFrame | None":
        try:
            text = raw.decode('ascii', errors='ignore').strip()
        except Exception:
            return None
        if not text.startswith(MODBUS_FRAME.START):
            return None
        body = text[1:]
        if len(body) < 6 or len(body) % 2 != 0:
            return None
        try:
            payload = bytes.fromhex(body)
        except ValueError:
            return None
        data = payload[:-1]
        checksum = payload[-1]
        if ModbusFrame.lrc(data) != checksum:
            return None
        return ModbusFrame(data[0], data[1], data[2:])

    def hex_preview(self) -> str:
        return self.encode().decode('ascii').strip()

class Modbus:
    def __init__(self, com: COM) -> None:
        self.com = com
        self.transaction_timeout: float = 1.0
        self.retries: int = 0
        self.inter_char_timeout: float = 1.0
        self._slave_address: int = MODBUS_LIMIT.MIN_SLAVE_ADDRESS
        self._slave_active = False
        self._slave_thread: threading.Thread | None = None
        self._received_text: str = ""
        self._stored_text: str = ""
        self._on_frame_sent = None
        self._on_frame_received = None

    def set_frame_callbacks(self, on_sent, on_received) -> None:
        self._on_frame_sent = on_sent
        self._on_frame_received = on_received

    def apply_inter_char_timeout(self) -> None:
        self.com.set_modbus_inter_char_timeout(self.inter_char_timeout)

    def _read_frame(self) -> ModbusFrame | None:
        raw = self.com.read_modbus()
        if not raw:
            return None
        frame = ModbusFrame.decode(raw)
        if frame is not None and self._on_frame_received is not None:
            self._on_frame_received(frame.hex_preview())
        return frame

    def _send_frame(self, frame: ModbusFrame) -> bool:
        if not self.com.conn_port or not self.com.conn_port.is_open:
            return False
        if self._on_frame_sent is not None:
            self._on_frame_sent(frame.hex_preview())
        return bool(self.com.conn_port.write(frame.encode()))

    def master_transaction(self, address: int, command: int, data: bytes) -> "ModbusFrame | MODBUS_ERROR":
        if not self.com.conn_port or not self.com.conn_port.is_open:
            return MODBUS_ERROR.NO_CONNECTION
        self.apply_inter_char_timeout()
        frame = ModbusFrame(address, command, data)
        if address == MODBUS_LIMIT.BROADCAST_ADDRESS:
            self._send_frame(frame)
            return frame
        attempt = 0
        while attempt <= self.retries:
            self._drain_input()
            self._send_frame(frame)
            response = self._await_response(address)
            if isinstance(response, ModbusFrame):
                if response.command & 0x80:
                    return MODBUS_ERROR.EXCEPTION_RESPONSE
                return response
            attempt += 1
        return MODBUS_ERROR.TRANSACTION_TIMEOUT

    def _drain_input(self) -> None:
        while self._read_frame() is not None:
            pass

    def _await_response(self, address: int) -> "ModbusFrame | MODBUS_ERROR":
        deadline = time.perf_counter() + self.transaction_timeout
        while time.perf_counter() < deadline:
            frame = self._read_frame()
            if frame is not None and frame.address == address:
                return frame
            time.sleep(0.01)
        return MODBUS_ERROR.NO_RESPONSE

    def write_text(self, address: int, text: str) -> "ModbusFrame | MODBUS_ERROR":
        return self.master_transaction(address, MODBUS_CMD.WRITE_TEXT, text.encode('utf-8'))

    def read_text(self, address: int) -> "ModbusFrame | MODBUS_ERROR":
        return self.master_transaction(address, MODBUS_CMD.READ_TEXT, b"")

    def start_slave(self, address: int) -> None:
        self._slave_address = address
        self.apply_inter_char_timeout()
        self._slave_active = True
        self._slave_thread = threading.Thread(target=self._slave_loop, daemon=True)
        self._slave_thread.start()

    def stop_slave(self) -> None:
        self._slave_active = False

    def _slave_loop(self) -> None:
        while self._slave_active:
            try:
                frame = self._read_frame()
                if frame is None:
                    time.sleep(0.01)
                    continue
                if frame.address != self._slave_address and frame.address != MODBUS_LIMIT.BROADCAST_ADDRESS:
                    continue
                self._handle_request(frame)
            except Exception:
                time.sleep(0.01)

    def _handle_request(self, frame: ModbusFrame) -> None:
        broadcast = frame.address == MODBUS_LIMIT.BROADCAST_ADDRESS
        if frame.command == MODBUS_CMD.WRITE_TEXT:
            self._received_text = frame.data.decode('utf-8', errors='ignore')
            if not broadcast:
                response = ModbusFrame(self._slave_address, MODBUS_CMD.WRITE_TEXT, b"")
                self._send_frame(response)
        elif frame.command == MODBUS_CMD.READ_TEXT:
            if not broadcast:
                response = ModbusFrame(self._slave_address, MODBUS_CMD.READ_TEXT, self._stored_text.encode('utf-8'))
                self._send_frame(response)
        else:
            if not broadcast:
                response = ModbusFrame(self._slave_address, frame.command | 0x80, bytes([MODBUS_EXCEPTION.ILLEGAL_FUNCTION]))
                self._send_frame(response)

    def get_received_text(self) -> str:
        return self._received_text

    def set_stored_text(self, text: str) -> None:
        self._stored_text = text
