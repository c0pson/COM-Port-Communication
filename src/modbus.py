import customtkinter as ctk # type: ignore

import threading

from const import LOG_LEVEL, COLOR
from notification import Notification
from serial_com import COM
from logger import Logger
from modbus_prot import Modbus, ModbusFrame, MODBUS_ERROR
from const import MODBUS_MODE, MODBUS_LIMIT, MODBUS_MESSAGE

class ModbusUI(ctk.CTkFrame):
    def __init__(self, master, logger, com: COM) -> None:
        super().__init__(master, fg_color=COLOR.BACKGROUND)
        self.logger: Logger = logger
        self.setup_font()
        self.setup_modbus(com)
        self.setup_GUI()
        self.setup_notifications()
        self.logger.log(LOG_LEVEL.INFO, "Modbus view initialized successfully")

    def setup_font(self) -> None:
        self.font_21 = ctk.CTkFont("Ubuntu Mono", 21, weight='bold')
        self.font_18 = ctk.CTkFont("Ubuntu Mono", 18, weight='bold')
        self.font_13 = ctk.CTkFont("Ubuntu Mono", 13, weight='bold')

    def setup_modbus(self, com: COM) -> None:
        self.com = com
        self.modbus = Modbus(com)
        self.modbus.set_frame_callbacks(self.on_frame_sent, self.on_frame_received)
        self.slave_running: bool = False
        self.continuous_mode: bool = False

    def setup_GUI(self) -> None:
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)
        self.rowconfigure(1, weight=1)
        self.top_frame().grid(row=0, column=0, columnspan=3, sticky="ew", padx=5, pady=5)
        self.left_toolbar().grid(row=1, column=0, sticky="nsw", padx=5, pady=5)
        self.write_frame().grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
        self.read_frame().grid(row=1, column=2, sticky="nsew", padx=5, pady=5)

    def setup_notifications(self) -> None:
        self.pending_notification: None | str = None
        self.notifications: list[Notification] = []

    def write_frame(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self, fg_color=COLOR.BACKGROUND)
        bottom_frame = ctk.CTkFrame(frame, fg_color=COLOR.BACKGROUND)
        bottom_frame.pack(side=ctk.BOTTOM, fill=ctk.X, pady=2, padx=2)
        self.text_input = ctk.CTkTextbox(
            master=frame,
            font=self.font_18
        )
        self.text_input.pack(side=ctk.TOP, padx=0, pady=0, expand=True, fill=ctk.BOTH)
        self.send_text_button = ctk.CTkButton(
            master=bottom_frame,
            font=self.font_21,
            text="Send Text",
            command=self.send_text,
            text_color=COLOR.TEXT_MAIN,
            fg_color=COLOR.ACCENT_2
        )
        self.send_text_button.pack(side=ctk.LEFT, padx=5, pady=2, anchor=ctk.CENTER, expand=True)
        self.read_text_button = ctk.CTkButton(
            master=bottom_frame,
            font=self.font_21,
            text="Read Text",
            command=self.request_text,
            text_color=COLOR.TEXT_MAIN,
            fg_color=COLOR.ACCENT_2
        )
        self.read_text_button.pack(side=ctk.LEFT, padx=5, pady=2, anchor=ctk.CENTER, expand=True)
        self.input_clear_button = ctk.CTkButton(
            master=bottom_frame,
            font=self.font_21,
            text="Clear",
            command=self.clear_input,
            text_color=COLOR.TEXT_MAIN,
            fg_color=COLOR.ACCENT_2
        )
        self.input_clear_button.pack(side=ctk.LEFT, padx=5, pady=2, anchor=ctk.CENTER, expand=True)
        return frame

    def read_frame(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self, fg_color=COLOR.BACKGROUND)
        self.text_intake = ctk.CTkTextbox(
            master=frame,
            state="disabled",
            font=self.font_18
        )
        self.text_intake.pack(side=ctk.TOP, padx=0, pady=0, expand=True, fill=ctk.BOTH)
        ctk.CTkButton(
            master=frame,
            font=self.font_21,
            text="Clear Log",
            command=self.clear_log,
            text_color=COLOR.TEXT_MAIN,
            fg_color=COLOR.ACCENT_2
        ).pack(side=ctk.TOP, padx=5, pady=5, anchor=ctk.CENTER)
        self.frame_log = ctk.CTkTextbox(
            master=frame,
            state="disabled",
            font=self.font_18,
            height=140
        )
        self.frame_log.pack(side=ctk.TOP, padx=0, pady=(0,2), fill=ctk.BOTH)
        ctk.CTkButton(
            master=frame,
            font=self.font_21,
            text="Clear",
            command=self.clear_intake,
            text_color=COLOR.TEXT_MAIN,
            fg_color=COLOR.ACCENT_2
        ).pack(side=ctk.LEFT, padx=5, pady=5, anchor=ctk.CENTER, expand=True)
        return frame

    def top_frame(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self, fg_color=COLOR.ACCENT_1)
        ctk.CTkLabel(frame, text="Mode: ", height=46, font=self.font_21, text_color=COLOR.TEXT_MAIN).pack(side=ctk.LEFT, padx=(7, 0), pady=0)
        self.mode_var = ctk.StringVar(value=MODBUS_MODE.MASTER)
        self.mode_menu = ctk.CTkComboBox(
            master=frame,
            variable=self.mode_var,
            values=[MODBUS_MODE.MASTER, MODBUS_MODE.SLAVE],
            font=self.font_21,
            state="readonly",
            command=self.on_mode_change,
            text_color=COLOR.TEXT_MAIN,
            border_color=COLOR.ACCENT_2,
            button_color=COLOR.ACCENT_2,
            dropdown_text_color=COLOR.TEXT_FADE,
            dropdown_fg_color=COLOR.BACKGROUND
        )
        self.mode_menu.pack(side=ctk.LEFT, padx=7)
        self.slave_button = ctk.CTkButton(
            master=frame,
            text="Start Slave",
            command=self.toggle_slave,
            font=self.font_21,
            text_color=COLOR.TEXT_MAIN,
            fg_color=COLOR.ACCENT_2
        )
        return frame

    def left_toolbar(self) -> ctk.CTkFrame:
        self.rowconfigure(1, weight=1)
        frame = ctk.CTkFrame(self, fg_color=COLOR.ACCENT_1)
        ctk.CTkLabel(
            master=frame,
            text="Modbus settings  ",
            font=self.font_21,
            text_color=COLOR.TEXT_MAIN
        ).pack(side=ctk.TOP, padx=7, pady=7, anchor=ctk.W)
        # Slave address settings
        def validate_address_input(new_value):
            if new_value == "":
                return True
            if not new_value.isdigit():
                return False
            return MODBUS_LIMIT.BROADCAST_ADDRESS <= int(new_value) <= MODBUS_LIMIT.MAX_SLAVE_ADDRESS
        ctk.CTkLabel(
            master=frame,
            text="Slave address (0-247)",
            font=self.font_18,
            text_color=COLOR.TEXT_MAIN
        ).pack(anchor="w", padx=7)
        self.address_var = ctk.StringVar(value="1")
        vcmd_address = self.register(validate_address_input)
        ctk.CTkEntry(
            master=frame,
            textvariable=self.address_var,
            validate="key",
            validatecommand=(vcmd_address, "%P"),
            font=self.font_18,
            text_color=COLOR.TEXT_FADE
        ).pack(padx=7, pady=(0,7), fill="x")
        # Transaction timeout settings
        def validate_timeout_input(new_value):
            if new_value == "":
                return True
            parts = new_value.split(".")
            if len(parts) > 2:
                return False
            if not parts[0].isdigit() and parts[0] != "":
                return False
            if len(parts) == 2 and not parts[1].isdigit() and parts[1] != "":
                return False
            try:
                return float(new_value) <= 10
            except ValueError:
                return True
        ctk.CTkLabel(
            master=frame,
            text="Transaction timeout (s)",
            font=self.font_18,
            text_color=COLOR.TEXT_MAIN
        ).pack(anchor="w", padx=7)
        self.timeout_var = ctk.StringVar(value="1")
        vcmd_timeout = self.register(validate_timeout_input)
        ctk.CTkEntry(
            master=frame,
            textvariable=self.timeout_var,
            validate="key",
            validatecommand=(vcmd_timeout, "%P"),
            font=self.font_18,
            text_color=COLOR.TEXT_FADE
        ).pack(padx=7, pady=(0,7), fill="x")
        # Retransmission settings
        ctk.CTkLabel(
            master=frame,
            text="Retransmissions (0-5)",
            font=self.font_18,
            text_color=COLOR.TEXT_MAIN
        ).pack(anchor="w", padx=7)
        self.retries_var = ctk.StringVar(value="0")
        ctk.CTkComboBox(
            master=frame,
            variable=self.retries_var,
            values=["0", "1", "2", "3", "4", "5"],
            font=self.font_21,
            state="readonly",
            text_color=COLOR.TEXT_FADE,
            dropdown_text_color=COLOR.TEXT_FADE
        ).pack(padx=7, pady=(0,7), fill="x")
        # Inter-character timeout settings
        def validate_inter_char_input(new_value):
            if new_value == "":
                return True
            parts = new_value.split(".")
            if len(parts) > 2:
                return False
            if not parts[0].isdigit() and parts[0] != "":
                return False
            if len(parts) == 2 and not parts[1].isdigit() and parts[1] != "":
                return False
            try:
                return float(new_value) <= 1
            except ValueError:
                return True
        ctk.CTkLabel(
            master=frame,
            text="Inter-char timeout (s)",
            font=self.font_18,
            text_color=COLOR.TEXT_MAIN
        ).pack(anchor="w", padx=7)
        self.inter_char_var = ctk.StringVar(value="0.1")
        vcmd_inter_char = self.register(validate_inter_char_input)
        ctk.CTkEntry(
            master=frame,
            textvariable=self.inter_char_var,
            validate="key",
            validatecommand=(vcmd_inter_char, "%P"),
            font=self.font_18,
            text_color=COLOR.TEXT_FADE
        ).pack(padx=7, pady=(0,7), fill="x")
        return frame

    def on_mode_change(self, value: str) -> None:
        if value == MODBUS_MODE.SLAVE:
            self.slave_button.pack(side=ctk.RIGHT, padx=7, pady=7)
            self.send_text_button.pack_forget()
            self.read_text_button.pack_forget()
        else:
            if self.slave_running:
                self.toggle_slave()
            self.slave_button.pack_forget()
            self.send_text_button.pack(side=ctk.LEFT, padx=5, pady=2, anchor=ctk.CENTER, expand=True, before=self.input_clear_button)
            self.read_text_button.pack(side=ctk.LEFT, padx=5, pady=2, anchor=ctk.CENTER, expand=True, before=self.input_clear_button)

    def apply_master_params(self) -> None:
        self.modbus.transaction_timeout = float(self.timeout_var.get() or 1)
        self.modbus.retries = int(self.retries_var.get())
        self.modbus.inter_char_timeout = float(self.inter_char_var.get() or 0.1)

    def toggle_slave(self) -> None:
        if not self.com.conn_port or not self.com.conn_port.is_open:
            self.logger.log(LOG_LEVEL.WARNING, "Slave toggle failed: no connection")
            self.create_notification(MODBUS_MESSAGE.NO_CONNECTION)
            return
        if not self.slave_running:
            address = int(self.address_var.get() or MODBUS_LIMIT.MIN_SLAVE_ADDRESS)
            self.modbus.inter_char_timeout = float(self.inter_char_var.get() or 0.1)
            self.modbus.set_stored_text(self.text_input.get("1.0", "end-1c"))
            self.modbus.start_slave(address)
            self.slave_running = True
            self.slave_button.configure(text="Stop Slave")
            self.logger.log(LOG_LEVEL.INFO, f"Slave started at address {address}")
            self.create_notification(MODBUS_MESSAGE.SLAVE_LISTENING)
            self.start_slave_polling()
        else:
            self.modbus.stop_slave()
            self.slave_running = False
            self.slave_button.configure(text="Start Slave")
            self.logger.log(LOG_LEVEL.INFO, "Slave stopped")
            self.create_notification(MODBUS_MESSAGE.SLAVE_STOPPED)

    def start_slave_polling(self) -> None:
        if self.slave_running:
            self.modbus.set_stored_text(self.text_input.get("1.0", "end-1c"))
            received = self.modbus.get_received_text()
            current = self.text_intake.get("1.0", "end-1c")
            if received and received != current:
                self.text_intake.configure(state="normal")
                self.text_intake.delete("1.0", ctk.END)
                self.text_intake.insert(ctk.END, received)
                self.text_intake.configure(state="disabled")
            self.after(50, self.start_slave_polling)

    def send_text(self) -> None:
        if not self.com.conn_port or not self.com.conn_port.is_open:
            self.logger.log(LOG_LEVEL.WARNING, "Send attempt failed: no connection")
            self.create_notification(MODBUS_MESSAGE.NO_CONNECTION)
            return
        self.apply_master_params()
        address = int(self.address_var.get() or MODBUS_LIMIT.MIN_SLAVE_ADDRESS)
        text = self.text_input.get("1.0", "end-1c")
        self.logger.log(LOG_LEVEL.INFO, f"Sending text to slave {address}: {repr(text)}")
        threading.Thread(target=self._send_text, args=(address, text), daemon=True).start()

    def _send_text(self, address: int, text: str) -> None:
        result = self.modbus.write_text(address, text)
        self.after(0, lambda: self._handle_result(result, MODBUS_MESSAGE.TEXT_WRITTEN, broadcast=(address == MODBUS_LIMIT.BROADCAST_ADDRESS)))

    def request_text(self) -> None:
        if not self.com.conn_port or not self.com.conn_port.is_open:
            self.logger.log(LOG_LEVEL.WARNING, "Read attempt failed: no connection")
            self.create_notification(MODBUS_MESSAGE.NO_CONNECTION)
            return
        self.apply_master_params()
        address = int(self.address_var.get() or MODBUS_LIMIT.MIN_SLAVE_ADDRESS)
        if address == MODBUS_LIMIT.BROADCAST_ADDRESS:
            self.logger.log(LOG_LEVEL.WARNING, "Read failed: broadcast not allowed for read")
            self.create_notification(MODBUS_MESSAGE.INVALID_ADDRESS)
            return
        self.logger.log(LOG_LEVEL.INFO, f"Requesting text from slave {address}")
        threading.Thread(target=self._request_text, args=(address,), daemon=True).start()

    def _request_text(self, address: int) -> None:
        result = self.modbus.read_text(address)
        self.after(0, lambda: self._handle_read_result(result))

    def _handle_result(self, result, success_message: str, broadcast: bool = False) -> None:
        if isinstance(result, ModbusFrame):
            if broadcast:
                self.logger.log(LOG_LEVEL.INFO, "Broadcast sent")
                self.create_notification(MODBUS_MESSAGE.BROADCAST_SENT)
            else:
                self.logger.log(LOG_LEVEL.INFO, "Transaction successful")
                self.create_notification(success_message)
            return
        self._handle_error(result)

    def _handle_read_result(self, result) -> None:
        if isinstance(result, ModbusFrame):
            text = result.data.decode('utf-8', errors='ignore')
            self.logger.log(LOG_LEVEL.INFO, f"Text read: {repr(text)}")
            self.text_intake.configure(state="normal")
            self.text_intake.delete("1.0", ctk.END)
            self.text_intake.insert(ctk.END, text)
            self.text_intake.configure(state="disabled")
            self.create_notification(MODBUS_MESSAGE.TEXT_READ)
            return
        self._handle_error(result)

    def _handle_error(self, result) -> None:
        match result:
            case MODBUS_ERROR.NO_CONNECTION:
                self.logger.log(LOG_LEVEL.WARNING, "Transaction failed: no connection")
                self.create_notification(MODBUS_MESSAGE.NO_CONNECTION)
            case MODBUS_ERROR.TRANSACTION_TIMEOUT:
                self.logger.log(LOG_LEVEL.WARNING, "Transaction failed: timeout")
                self.create_notification(MODBUS_MESSAGE.TRANSACTION_TIMEOUT)
            case MODBUS_ERROR.NO_RESPONSE:
                self.logger.log(LOG_LEVEL.WARNING, "Transaction failed: no response")
                self.create_notification(MODBUS_MESSAGE.NO_RESPONSE)
            case MODBUS_ERROR.INVALID_LRC:
                self.logger.log(LOG_LEVEL.WARNING, "Transaction failed: invalid LRC")
                self.create_notification(MODBUS_MESSAGE.INVALID_LRC)
            case MODBUS_ERROR.EXCEPTION_RESPONSE:
                self.logger.log(LOG_LEVEL.WARNING, "Transaction failed: exception response")
                self.create_notification(MODBUS_MESSAGE.EXCEPTION_RESPONSE)

    def on_frame_sent(self, hex_frame: str) -> None:
        self.after(0, lambda: self._append_log(f"TX  {hex_frame}"))

    def on_frame_received(self, hex_frame: str) -> None:
        self.after(0, lambda: self._append_log(f"RX  {hex_frame}"))

    def _append_log(self, line: str) -> None:
        self.frame_log.configure(state="normal")
        self.frame_log.insert(ctk.END, line + "\n")
        self.frame_log.see(ctk.END)
        self.frame_log.configure(state="disabled")

    def clear_log(self) -> None:
        self.frame_log.configure(state="normal")
        self.frame_log.delete("1.0", ctk.END)
        self.frame_log.configure(state="disabled")

    def clear_input(self) -> None:
        self.text_input.delete("1.0", ctk.END)

    def clear_intake(self) -> None:
        self.text_intake.configure(state="normal")
        self.text_intake.delete("1.0", ctk.END)
        self.text_intake.configure(state="disabled")

    def create_notification(self, message: str):
        if self.notifications:
            self.destroy_notifications()
        if self.pending_notification:
            self.after_cancel(self.pending_notification)
            self.pending_notification = None
        self.notifications.append(Notification(self, message, 3, "top"))

    def destroy_notifications(self):
        for notification in self.notifications:
            notification.destroy()
        self.notifications[:] = []
