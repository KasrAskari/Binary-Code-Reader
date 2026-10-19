"""
main.py

Entry point of Binary Code Reader.
"""

import sys
import tkinter as tk
import traceback
from tkinter import messagebox

from errorlog import log_exception
from gui import run


def _report_callback_exception(_app, exc_type, exc_value, exc_tb) -> None:
    
    """
    Handle errors raised inside Tkinter callbacks (button clicks etc.).

    Tkinter's default handler prints to the console, which a windowed
    .exe does not have. So we log to a file and tell the user.
    """
    
    path = log_exception(exc_type, exc_value, exc_tb)
    if sys.stderr is not None:  # during development, keep the traceback visible
        traceback.print_exception(exc_type, exc_value, exc_tb)
    where = f"Details were saved to:\n{path}" if path else "The log file could not be written."
    messagebox.showerror("Unexpected error", f"Something went wrong.\n\n{where}")


def main() -> None:
    tk.Tk.report_callback_exception = _report_callback_exception
    try:
        run()
    except Exception:
        log_exception(*sys.exc_info())  # errors before/after the main loop
        raise


if __name__ == "__main__":
    main()