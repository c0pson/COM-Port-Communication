import customtkinter as ctk # type: ignore

import threading
import re

from notification import Notification, MESSAGE
from serial_com import COM, ERROR

class App(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        font = ctk.FontManager()
        font.init_font_manager()
        font.load_font("font\\UbuntuMono-Regular.ttf")
        self.font_21 = ctk.CTkFont("Ubuntu Mono", 21)
        self.font_18 = ctk.CTkFont("Ubuntu Mono", 18)
        self.com = COM()
        self.all_devices = self.com.get_all_devices()
        self.continuous_mode: bool = False
        self.ping_mode: bool = False
        self.ping_thread: threading.Thread | None = None
        self.setup()
        self.geometry("1060x620")
        self.title("COM Port Communication")
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.notifications: list[Notification] = []

    def setup(self) -> None:
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)
        self.rowconfigure(1, weight=1)
        self.top_frame().grid(row=0, column=0, columnspan=3, sticky="ew", padx=5, pady=5)
        self.left_toolbar().grid(row=1, column=0, sticky="nsw", padx=5, pady=5)
        self.write_frame().grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
        self.read_frame().grid(row=1, column=2, sticky="nsew", padx=5, pady=5)

    def write_frame(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self)
        bottom_frame = ctk.CTkFrame(frame)
        bottom_frame.pack(side=ctk.BOTTOM, fill=ctk.X, pady=2, padx=2)
        self.text_input = ctk.CTkTextbox(
            master=frame,
            font=self.font_18
        )
        self.text_input.pack(side=ctk.TOP, padx=0, pady=0, expand=True, fill=ctk.BOTH)
        self.write_button = ctk.CTkButton(
            master=bottom_frame,
            font=self.font_21,
            text="Write",
            command=self.write
        )
        self.write_button.pack(side=ctk.LEFT, padx=5, pady=2, anchor=ctk.CENTER, expand=True)
        ctk.CTkButton(
            master=bottom_frame,
            font=self.font_21,
            text="Clear",
            command=self.clear_input
        ).pack(side=ctk.LEFT, padx=5, pady=2, anchor=ctk.CENTER, expand=True)
        return frame

    def read_frame(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self)
        bottom_frame = ctk.CTkFrame(frame)
        bottom_frame.pack(side=ctk.BOTTOM, fill=ctk.X, pady=2, padx=2)
        self.text_intake = ctk.CTkTextbox(
            master=frame,
            state="disabled",
            font=self.font_18
        )
        self.read_button = ctk.CTkButton(
            master=bottom_frame,
            font=self.font_21,
            text="Read",
            command=self.read
        )
        self.continuous_mode_check_button = ctk.CTkCheckBox(
            master=bottom_frame,
            font=self.font_21,
            text="Continuous mode",
            command=self.toggle_continuous_mode
        )
        self.continuous_mode_check_button.pack(side=ctk.LEFT, padx=5, pady=2, anchor=ctk.CENTER, expand=True)
        self.read_button.pack(side=ctk.LEFT, padx=5, pady=2, anchor=ctk.CENTER)
        self.text_intake.pack(side=ctk.TOP, padx=0, pady=0, expand=True, fill=ctk.BOTH)
        ctk.CTkButton(
            master=bottom_frame,
            font=self.font_21,
            text="Clear",
            command=self.clear_intake
        ).pack(side=ctk.LEFT, padx=5, pady=2, anchor=ctk.CENTER, expand=True)
        return frame

    def top_frame(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self)
        ctk.CTkLabel(frame, text="Port: ", font=self.font_21).pack(side=ctk.LEFT, padx=(7, 0))
        longest = max((len(p.name) for p in self.all_devices), default=10)
        self.port_var = ctk.StringVar()
        self.ports_menu = ctk.CTkComboBox(
            master=frame,
            variable=self.port_var,
            values=[p.name for p in self.all_devices],
            width=longest * 8,
            state="readonly"
        )
        self.ports_menu.pack(side=ctk.LEFT)
        ctk.CTkButton(
            master=frame,
            text="Connect",
            command=self.connect,
            font=self.font_21
        ).pack(side=ctk.RIGHT, padx=7, pady=7)
        self.ping_button = ctk.CTkButton(
            master=frame,
            text="Ping",
            command=self.ping,
            font=self.font_21
        )
        self.ping_button.pack(side=ctk.RIGHT, padx=7, pady=7)
        self.toggle_ping_button = ctk.CTkCheckBox(
            master=frame,
            width=0, # some customtkinter weird behavior while scaling background of the widget 
            text="Listen mode",
            font=self.font_21,
            command=self.toggle_ping_mode,
        )
        self.toggle_ping_button.pack(side=ctk.RIGHT)
        self.ping_measurement_label = ctk.CTkLabel(
            master=frame,
            text="Ping: ---ms",
            font=self.font_21
        )
        self.ping_measurement_label.pack(side=ctk.RIGHT, expand=True, padx=10, pady=7)
        return frame

    def left_toolbar(self) -> ctk.CTkFrame:
        self.rowconfigure(1, weight=1)
        frame = ctk.CTkFrame(self)
        ctk.CTkLabel(
            master=frame,
            text="Port settings",
            font=self.font_21
        ).pack(side=ctk.TOP, padx=7, pady=7, anchor=ctk.W)

        ctk.CTkLabel(
            master=frame,
            text="Baudrate",
            font=self.font_18
        ).pack(anchor="w", padx=7)
        self.baud_var = ctk.StringVar(value="9600")
        ctk.CTkComboBox(
            master=frame,
            variable=self.baud_var,
            values=["150","300","600","1200","2400","4800","9600","19200","38400","57600","115200"],
            font=self.font_21,
            state="readonly"
        ).pack(padx=7, pady=(0,7), fill="x")

        ctk.CTkLabel(
            master=frame,
            text="Bytesize",
            font=self.font_18
        ).pack(anchor="w", padx=7)
        self.bytesize_var = ctk.StringVar(value="8")
        ctk.CTkComboBox(
            master=frame,
            variable=self.bytesize_var,
            values=["7", "8"],
            font=self.font_21,
            state="readonly"
        ).pack(padx=7, pady=(0,7), fill="x")

        ctk.CTkLabel(
            master=frame,
            text="Parity",
            font=self.font_18
        ).pack(anchor="w", padx=7)
        self.parity_var = ctk.StringVar(value="N")
        ctk.CTkComboBox(
            master=frame,
            variable=self.parity_var,
            values=["N", "E", "O"],
            font=self.font_21,
            state="readonly"
        ).pack(padx=7, pady=(0,7), fill="x")

        ctk.CTkLabel(
            master=frame,
            text="Stop bits",
            font=self.font_18
        ).pack(anchor="w", padx=7)
        self.stopbits_var = ctk.StringVar(value="1")
        ctk.CTkComboBox(
            master=frame,
            variable=self.stopbits_var,
            values=["1", "2"],
            font=self.font_21,
            state="readonly"
        ).pack(padx=7, pady=(0,7), fill="x")

        def validate_input(new_value):
            return new_value.isdigit() or new_value == ""
        ctk.CTkLabel(
            master=frame,
            text="Timeout (s)",
            font=self.font_18
        ).pack(anchor="w", padx=7)
        self.timeout_var = ctk.StringVar(value="1")
        vcmd = self.register(validate_input)
        ctk.CTkEntry(
            master=frame,
            textvariable=self.timeout_var,
            validate="key",
            validatecommand=(vcmd, "%P")
        ).pack(padx=7, pady=(0,7), fill="x")

        ctk.CTkLabel(
            master=frame,
            text="Flow control",
            font=self.font_18
        ).pack(anchor="w", padx=7)
        self.flow_var = ctk.StringVar(value="None")
        ctk.CTkComboBox(
            master=frame,
            variable=self.flow_var,
            values=["None", "XON/XOFF", "RTS/CTS", "DTR/DSR"],
            font=self.font_21,
            state="readonly"
        ).pack(padx=7, pady=(0,7), fill="x")

        ctk.CTkLabel(
            master=frame,
            text="Terminator",
            font=self.font_18
        ).pack(anchor="w", padx=7)
        self.terminator_var = ctk.StringVar(value="None")
        terminator_menu = ctk.CTkComboBox(
            master=frame,
            variable=self.terminator_var,
            values=["None", "CR", "LF", "CR-LF", "Custom"],
            font=self.font_21,
            state="readonly",
            command=self.on_terminator_change
        )
        terminator_menu.pack(padx=7, pady=(0,7), fill="x")

        def validate_terminator(new_value):
            return len(new_value) <= 2

        vcmd_term = self.register(validate_terminator)
        self.custom_terminator_frame = ctk.CTkFrame(frame)
        ctk.CTkLabel(
            master=self.custom_terminator_frame,
            text="Custom terminator",
            font=self.font_18
        ).pack(anchor="w", padx=7)
        self.custom_terminator_var = ctk.StringVar(value="")
        ctk.CTkEntry(
            master=self.custom_terminator_frame,
            textvariable=self.custom_terminator_var,
            validate="key",
            validatecommand=(vcmd_term, "%P")
        ).pack(padx=7, pady=(0,7), fill="x")

        return frame

    def check_connection(self):
        port = next((p for p in self.all_devices if p.name == self.port_var.get()), None)
        if not port:
            self.create_notification(MESSAGE.NO_CONNECTION)
            return False
        return True, port

    def on_terminator_change(self, value: str):
        if self.terminator_var.get() == "Custom":
            self.custom_terminator_frame.pack(padx=7, pady=(0,7), fill="x")
        else:
            self.custom_terminator_frame.pack_forget()

    def get_terminator(self) -> str:
        terminator_type = self.terminator_var.get()
        if terminator_type == "None":
            return ""
        elif terminator_type == "CR":
            return "\r"
        elif terminator_type == "LF":
            return "\n"
        elif terminator_type == "CR-LF":
            return "\r\n"
        elif terminator_type == "Custom":
            return self.custom_terminator_var.get()
        return ""

    def connect(self) -> None:
        if not (connection := self.check_connection()):
            return

        port = connection[1]
        flow_control = self.flow_var.get()
        xonxoff = flow_control == "XON/XOFF"
        rtscts = flow_control == "RTS/CTS"
        dsrdtr = flow_control == "DTR/DSR"
        
        try:
            self.com.connect(
                port,
                baudrate=int(self.baud_var.get()),
                bytesize=int(self.bytesize_var.get()),
                parity=self.parity_var.get(),
                stopbits=int(self.stopbits_var.get()),
                timeout=float(self.timeout_var.get()),
                xonxoff=xonxoff,
                rtscts=rtscts,
                dsrdtr=dsrdtr
            )
            self.create_notification("Connection Successful")
        except Exception as e:
            match = re.search(r"'([^']+)'[^']*$", str(e))
            err = match.group(1) if match else "Unknown Error"
            self.create_notification(MESSAGE.ERROR_UNKNOWN)

    def ping(self):
        if self.ping_mode:
            return
        self.create_notification(MESSAGE.PING_INFO)
        self.after(3501, self._ping)

    def _ping(self):
        match self.com.ping():
            case ERROR.NO_CONNECTION:
                self.create_notification(MESSAGE.NO_CONNECTION)
            case ERROR.CONNECTION_FAILURE:
                self.create_notification(MESSAGE.CONNECTION_ERROR)
            case _: ...

    def toggle_ping_mode(self):
        if self.ping_mode:
            self.ping_mode = False
            self.ping_button.configure(state="normal")
            self.write_button.configure(state="normal")
            self.read_button.configure(state="normal")
        else:
            if not self.com.conn_port or not self.com.conn_port.is_open:
                self.create_notification(MESSAGE.NO_CONNECTION)
                self.toggle_ping_button.deselect()
                return
            self.ping_button.configure(state="disabled")
            self.write_button.configure(state="disabled")
            self.read_button.configure(state="disabled")
            self.ping_mode = True
            self.ping_thread = threading.Thread(target=self._ping_loop, daemon=True)
            self.ping_thread.start()

    def _ping_loop(self):
        while self.ping_mode:
            try:
                if not self.com.conn_port or not self.com.conn_port.is_open:
                    self.after(0, self._stop_ping_mode)
                    break
                ping_ms = self.com.return_ping()
                if ping_ms > 0:
                    self.after(0, lambda: self._update_ping_label(ping_ms))
                    self.toggle_ping_button.deselect()
                else:
                    self.after(0, self._stop_ping_mode)
                    break
            except Exception as e:
                print(f"Ping error: {e}")
                self.after(0, self._stop_ping_mode)
                break

    def _update_ping_label(self, ping_ms: float):
        self.ping_measurement_label.configure(text=f"Ping: {ping_ms:.3f}ms")

    def _stop_ping_mode(self):
        self.toggle_ping_button.deselect()
        self.ping_mode = False
        self.ping_measurement_label.configure(text="Ping: ---ms")
        self.ping_button.configure(state="normal")
        self.write_button.configure(state="normal")
        self.read_button.configure(state="normal")

    def write(self):
        if not self.check_connection():
            self.create_notification(MESSAGE.NO_CONNECTION)
            return
        message = self.text_input.get("1.0", "end-1c")
        terminator = self.get_terminator()
        if self.com.write(message + terminator):
            self.create_notification(MESSAGE.WRITE_SUCCESS)
        else:
            self.create_notification(MESSAGE.WRITE_FAIL)

    def clear_input(self) -> None:
        self.text_input.delete("1.0", ctk.END)

    def clear_intake(self) -> None:
        self.text_intake.configure(state="normal")
        self.text_intake.delete("1.0", ctk.END)
        self.text_intake.configure(state="disabled")

    def toggle_continuous_mode(self):
        if not self.com.conn_port or not self.com.conn_port.is_open:
            self.create_notification(MESSAGE.NO_CONNECTION)
            self.continuous_mode_check_button.deselect()
            return
        if not self.continuous_mode:
            self.read_button.configure(state="disabled")
            self.continuous_mode = True
            self.start_continuous_mode()
        else:
            self.read_button.configure(state="normal")
            self.continuous_mode = False

    def start_continuous_mode(self):
        if self.continuous_mode:
            try:
                self.just_read()
            except Exception as e:
                print(e)
            self.after(21, self.start_continuous_mode)

    def just_read(self):
        if read_val := self.com.read():
            self.text_intake.configure(state="normal")
            self.text_intake.insert(ctk.END, read_val.decode('utf-8'))
            self.text_intake.configure(state="disabled")

    def read(self):
        if not self.check_connection():
            self.create_notification(MESSAGE.NO_CONNECTION)
            return
        if read_val := self.com.read():
            self.text_intake.configure(state="normal")
            self.text_intake.insert(ctk.END, read_val.decode('utf-8'))
            self.text_intake.configure(state="disabled")
            self.create_notification(MESSAGE.READ_SUCCESS)
        else:
            self.create_notification(MESSAGE.READ_FAIL)

    def create_notification(self, message: str):
        if self.notifications:
            self.destroy_notifications()
        self.notifications.append(Notification(self, message, 3, "top"))

    def destroy_notifications(self):
        for notification in self.notifications:
            notification.destroy()
        self.notifications[:] = []

    def on_close(self):
        self.com.disconnect()
        self.destroy()

if __name__ == "__main__":
    app = App()
    app.mainloop()
