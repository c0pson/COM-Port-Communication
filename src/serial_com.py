import serial.tools.list_ports # type: ignore

from dataclasses import dataclass

@dataclass
class COMPort:
    name: str
    port: str

class COM:
    def __init__(self):
        self.conn_port = None

    def get_all_devices(self) -> list[COMPort]:
        ports: list[COMPort] = []
        all_ports = serial.tools.list_ports.comports()
        for port in all_ports:
            if port.vid is not None:
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
        self.conn_port = serial.Serial(
            port=COMPort.port,
            baudrate=baudrate,
            bytesize=bytesize,
            parity=parity,
            stopbits=stopbits,
            timeout=timeout,
            xonxoff=xonxoff,
            rtscts=rtscts,
            write_timeout=write_timeout,
            dsrdtr=dsrdtr,
            inter_byte_timeout=inter_byte_timeout,
            exclusive=exclusive
        )

    def disconnect(self) -> None:
        if self.conn_port and self.conn_port.is_open:
            self.conn_port.close()
            self.conn_port = None

    def write(self, message: str) -> bool:
        if not self.conn_port or not self.conn_port.is_open:
            return False
        if self.conn_port.write(message.encode('utf-8')):
            return True
        return False

    def read(self) -> bool | bytes:
        if not self.conn_port or not self.conn_port.is_open:
            return False
        if x := self.conn_port.read(self.conn_port.in_waiting):
            return x
        return False
