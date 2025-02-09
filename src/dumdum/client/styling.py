import sys
from tkinter import Tk
from tkinter.ttk import Style


def apply_style(app: Tk) -> None:
    style = Style(app)
    style.configure(".", background="white")


def enable_windows_dpi_awareness() -> None:
    if sys.platform == "win32":
        from ctypes import windll

        windll.shcore.SetProcessDpiAwareness(2)
