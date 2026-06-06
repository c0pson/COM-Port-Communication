import customtkinter as ctk # type: ignore

import re

from notification import Notification
from serial_com import COM

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
        self.setup()
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
        self.text_input = ctk.CTkTextbox(
            master=frame,
            font=self.font_18
        )
        self.text_input.pack(side=ctk.TOP, padx=0, pady=0, expand=True, fill=ctk.BOTH)
        ctk.CTkButton(
            master=frame,
            font=self.font_21,
            text="Write",
            command=self.write
        ).pack(side=ctk.BOTTOM, padx=5, pady=2, anchor=ctk.CENTER)
        return frame

    def read_frame(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self)
        self.text_intake = ctk.CTkTextbox(
            master=frame,
            state="disabled",
            font=self.font_18
        )
        ctk.CTkButton(
            master=frame,
            font=self.font_21,
            text="Read",
            command=self.read
        ).pack(side=ctk.BOTTOM, padx=5, pady=2, anchor=ctk.CENTER)
        self.text_intake.pack(side=ctk.TOP, padx=0, pady=0, expand=True, fill=ctk.BOTH)
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
        ctk.CTkButton(frame, text="Connect", command=self.connect, font=self.font_21).pack(side=ctk.RIGHT, padx=7, pady=7)
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

        return frame

    def check_connection(self):
        port = next((p for p in self.all_devices if p.name == self.port_var.get()), None)
        if not port:
            self.create_notification("No port selected")
            return False
        return True, port

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
            self.create_notification(err)

    def write(self):
        if not self.check_connection():
            self.create_notification("No connection")
            return
        message = self.text_input.get("1.0", "end-1c")
        if self.com.write(message):
            self.create_notification("Write Successful")
        else:
            self.create_notification("Writing Failure")

    def read(self):
        if not self.check_connection():
            self.create_notification("No connection")
            return
        if self.com.read():
            self.create_notification("Read Successful")
        else:
            self.create_notification("Reading Failure")

    def create_notification(self, message: str):
        if self.notifications:
            self.destroy_notifications()
        self.notifications.append(Notification(self, message, 3, "bottom_corner"))

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
