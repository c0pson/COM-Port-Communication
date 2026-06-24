# COM Port Communication

Desktop application for serial port communication with MODBUS-ASCII protocol support. Built with Python, customtkinter, and pyserial.

## File Tree

```
├── src/
│   ├── main.py             # App entry point, tab setup
│   ├── communication.py    # Task 1 GUI: port config, read/write, ping
│   ├── serial_com.py       # Core serial management, reader thread, ping/pong
│   ├── modbus.py           # Task 2 GUI: master/slave controls, frame log
│   ├── modbus_prot.py      # MODBUS-ASCII protocol logic, frame encode/decode
│   ├── const.py            # Enums and constants
│   ├── notification.py     # Animated notification overlay
│   ├── logger.py           # File logger
│   └── tools.py            # Resource path helper
├── font/
│   └── UbuntuMono-Regular.ttf
├── requirements.txt
└── run_virt_COM.ps1        # Launch two instances for virtual COM pair
```

## COM Port Communication

### 1.1 Port Selection

Available COM ports are detected via `pyserial` and filtered to physical or virtual devices. Selection is done through a dropdown.

```python
def get_all_devices(self) -> list[COMPort]:
    all_ports = serial.tools.list_ports.comports()
    for port in all_ports:
        if port.vid is not None or "Virtual" in port.description:
            ports.append(COMPort(port.description, port.device))
    return ports
```

### 1.2 Transmission Parameters

Baudrate (150–115200), bytesize (7/8), parity (N/E/O), and stop bits (1/2) are configurable via the left toolbar and passed directly to `serial.Serial()`.

### 1.3 Flow Control

Selectable between None, XON/XOFF, RTS/CTS, and DTR/DSR. Mapped to `serial.Serial` keyword arguments on connect.

```python
xonxoff = flow_control == "XON/XOFF"
rtscts  = flow_control == "RTS/CTS"
dsrdtr  = flow_control == "DTR/DSR"
self.com.connect(port, ..., xonxoff=xonxoff, rtscts=rtscts, dsrdtr=dsrdtr)
```

### 1.5 Terminator

Supports None, CR, LF, CR-LF, and a custom terminator (1–2 characters, length tied to stop bits). The terminator is appended automatically before each write.

```python
def get_terminator(self) -> str:
    match self.terminator_var.get():
        case "CR":    return "\r"
        case "LF":    return "\n"
        case "CR-LF": return "\r\n"
        case "Custom": return self.custom_terminator_var.get()
    return ""
```

### Text Transmit / Receive

Write sends the text input content plus terminator over the serial port. Read pulls data from a thread-safe queue. A continuous-mode checkbox enables auto-polling every 21 ms.

### Ping / Pong

Uses a token-based handshake with `sha1(urandom(8))` truncated to 8 hex chars. A background reader thread automatically responds to incoming `PING:` frames with `PONG:`. Round-trip latency is measured via `perf_counter`.

```python
def ping(self) -> float | ERROR:
    self._expected_token = self._make_ping_token()
    self._ping_sent_time = time.perf_counter()
    self.conn_port.write(f"PING:{self._expected_token}\n".encode('utf-8'))
    if self._pong_event.wait(timeout=1.0):
        return self._pong_time
    return ERROR.CONNECTION_FAILURE
```

### Reader Thread Architecture

A single daemon thread (`_reader_loop`) owns all serial reads. It routes traffic by inspecting the first byte:

- `:` → MODBUS frame assembly with inter-character gap timing
- `PING:` / `PONG:` → handled inline (auto-respond / measure latency)
- Everything else → queued for the GUI via `read_queue`

The serial port is opened with a fixed `timeout=0.1s` to avoid blocking; an empty-read sleep of 50 ms prevents CPU spin while keeping ping latency acceptable (~150 ms worst case).

## MODBUS-ASCII

### Frame Format

Frames follow standard MODBUS-ASCII: `:` start marker, hex-encoded payload (address + command + data + LRC), terminated with CR-LF.

```python
def encode(self) -> bytes:
    payload = bytes([self.address, self.command]) + self.data
    checksum = ModbusFrame.lrc(payload)
    ascii_body = (payload + bytes([checksum])).hex().upper()
    return f":{ascii_body}\r\n".encode('ascii')

@staticmethod
def lrc(payload: bytes) -> int:
    return ((~sum(payload) + 1) & 0xFF)
```

### Master Mode

Supports addressed and broadcast transactions. Configurable parameters:

| Parameter | Range | Default |
|---|---|---|
| Transaction timeout | 0–10 s | 1 s |
| Retransmissions | 0–5 | 0 |
| Inter-character timeout | 0–1 s | 0.1 s |

The master drains stale input before each attempt, sends the query frame, and waits for a matching response within the timeout. Retries are handled in a loop.

```python
def master_transaction(self, address, command, data):
    attempt = 0
    while attempt <= self.retries:
        self._drain_input()
        self._send_frame(frame)
        response = self._await_response(address)
        if isinstance(response, ModbusFrame):
            return response
        attempt += 1
    return MODBUS_ERROR.TRANSACTION_TIMEOUT
```

### Slave Mode

Runs a daemon thread polling for incoming frames. On each poll cycle the GUI refreshes the slave's stored text from the input textbox. Supported commands:

- **Command 1 (Write Text)** - stores received text, sends empty ACK (or silent on broadcast)
- **Command 2 (Read Text)** - returns the current stored text
- **Unknown command** - replies with exception code `ILLEGAL_FUNCTION` (0x80 flag)

### Inter-Character Timeout

MODBUS frames are assembled byte-by-byte inside `_read_modbus_frame` rather than using `readline()`. The maximum gap between consecutive characters is tracked; if any gap exceeds the configured inter-character timeout, the frame is discarded.

### Frame Log

All sent (TX) and received (RX) frames are displayed in a scrolling hex log at the bottom of the MODBUS tab via callbacks registered with `set_frame_callbacks`.

### Mode-Aware UI

Switching between Master and Slave hides/shows the relevant buttons, Send/Read buttons are hidden in Slave mode; the Start/Stop Slave button is hidden in Master mode.
