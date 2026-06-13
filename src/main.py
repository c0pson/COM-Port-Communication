import customtkinter as ctk # type: ignore

from logger import Logger, LOG_LEVEL
from time import time

from communication import Communication

class App(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.geometry("1160x720")
        self.title("COM Port Communication")
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.setup_logger()
        self.setup_tabs()
        self.comm_task = Communication(self.tab_view.tab("Communication"), self.logger)
        self.comm_task.pack(side=ctk.TOP, padx=0, pady=0, fill=ctk.BOTH, expand=True)

    def setup_tabs(self) -> None:
        self.tab_view = ctk.CTkTabview(self)
        self.tab_view.add("Communication")
        self.tab_view.add("ModBus")
        self.tab_view.pack(padx=0, pady=0, fill=ctk.BOTH, expand=True)

    def setup_logger(self) -> None:
        self.logger = Logger("logs", f"{time()}.log", level=LOG_LEVEL.INFO)
        self.logger.log(LOG_LEVEL.INFO, "Logger initialized")

    def on_close(self):
        self.logger.log(LOG_LEVEL.INFO, "Application closing")
        self.comm_task.com.disconnect()
        self.destroy()

if __name__ == "__main__":
    app = App()
    app.mainloop()
