import customtkinter as ctk # type: ignore

from logger import Logger, LOG_LEVEL
from time import time

from communication import Communication
from tools import resource_path
from modbus import ModbusUI
from const import COLOR

class App(ctk.CTk):
    def __init__(self) -> None:
        super().__init__(fg_color=COLOR.BACKGROUND)
        self.geometry("1160x720")
        self.title("COM Port Communication")
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        font = ctk.FontManager()
        font.init_font_manager()
        font.load_font(resource_path("font", "UbuntuMono-Regular.ttf"))
        self.font_21 = ctk.CTkFont("Ubuntu Mono", 21, weight='bold')

        self.setup_logger()
        self.setup_tabs()
        self.comm_task = Communication(self.tab_view.tab("Communication"), self.logger)
        self.comm_task.pack(side=ctk.TOP, padx=0, pady=0, fill=ctk.BOTH, expand=True)
        self.modbus_task = ModbusUI(self.tab_view.tab("ModBus"), self.logger, self.comm_task.com)
        self.modbus_task.pack(side=ctk.TOP, padx=0, pady=0, fill=ctk.BOTH, expand=True)

    def setup_tabs(self) -> None:
        self.tab_view = ctk.CTkTabview(self, fg_color=COLOR.BACKGROUND)
        self.tab_view._segmented_button.configure(
            font=self.font_21,
            fg_color=COLOR.ACCENT_1,
            selected_color=COLOR.ACCENT_2,
            selected_hover_color=COLOR.ACCENT_2,
            unselected_color=COLOR.ACCENT_1,
            unselected_hover_color=COLOR.ACCENT_2,
            text_color=COLOR.TEXT_MAIN,
        )
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
    ctk.deactivate_automatic_dpi_awareness()
    app = App()
    app.mainloop()
