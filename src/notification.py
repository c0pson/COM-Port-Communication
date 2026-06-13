import customtkinter as ctk # type: ignore
from typing import Any
import pywinstyles          # type: ignore

from enum import StrEnum

from const import MESSAGE

class Notification(ctk.CTkFrame):
    def __init__(self, master: Any, message: str, duration_sec: float, position: str='center', font_size: int=21):
        super().__init__(
            master        = master,
            fg_color      = None,
            corner_radius = 0,
            border_color  = None,
            border_width  = 3,
            width         = 1,
            height        = 1
        )
        self.font_name: str = "Ubuntu Mono"
        self.message: str = message
        self.duration: int = int(duration_sec * 1000)
        self.position: str = position
        self.font_size = font_size
        self.show_notification()

    def show_notification(self) -> None:
        self.text_label = ctk.CTkLabel(
            master     = self,
            text       = self.message,
            text_color = None, 
            font       = ctk.CTkFont(self.font_name, size=self.font_size),
            anchor     = ctk.N
        )
        self.text_label.pack(padx=10, pady=10)
        if self.position == 'center':
            self.place(relx=0.504, rely=0.47, anchor=ctk.CENTER)
        elif self.position == 'top':
            self.place(relx=0.5, y=20, anchor=ctk.N)
        elif self.position == 'bottom_corner':
            self.place(relx=0.99, rely=0.98, anchor=ctk.SE)
        else:
            self.place(relx=0.504, rely=0.47, anchor=ctk.CENTER)
        self.text_label.bind('<Button-1>', lambda e: self.hide_notification(0))
        self.show_animation(0)

    def show_animation(self, i: int) -> None:
        if not self.winfo_exists():
            return
        if i < 100:
            i += 1
            pywinstyles.set_opacity(self.winfo_id(), value=(0.01*i), color='#000001')
            self.master.after(1, lambda: self.show_animation(i))
        else:
            self.master.after(self.duration, lambda: self.hide_notification(0))

    def hide_notification(self, i: int) -> None:
        if i < 100:
            i += 1
            if self.winfo_exists():
                pywinstyles.set_opacity(self.winfo_id(), value=(1 - (0.01*i)), color='#000001')
                self.master.after(1, lambda: self.hide_notification(i))
        else:
            self.destroy()
