"""
gui.py

Tkinter interface for Binary Code Reader.
This module only handles display and user input.
Conversion logic lives in converter.py, file logic in files.py,
history logic in history.py, and persistence in settings.py / storage.py.
"""

import os
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, scrolledtext, ttk

from converter import (
    SUPPORTED_ENCODINGS,
    auto_convert,
    binary_to_text,
    text_to_binary,
)
from files import read_text_file, write_text_file
from history import History, HistoryEntry
from settings import load_settings, save_settings
from storage import default_config_dir, remove_file

# Drag & Drop is optional: without tkinterdnd2 the app still works
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD

    _TkBase = TkinterDnD.Tk
    DND_AVAILABLE = True
except ImportError:
    _TkBase = tk.Tk
    DND_AVAILABLE = False

HISTORY_MAX_SOURCE = 10_000  # longer inputs are not stored in history

THEMES = {
    "light": {
        "bg": "#f5f5f5",
        "fg": "#1e1e1e",
        "text_bg": "#ffffff",
        "text_fg": "#1e1e1e",
        "button_bg": "#e0e0e0",
        "button_active": "#d0d0d0",
        "border": "#b0b0b0",
        "select_bg": "#bbdefb",
        "error": "#c62828",
        "success": "#2e7d32",
    },
    "dark": {
        "bg": "#1e1e1e",
        "fg": "#e0e0e0",
        "text_bg": "#2b2b2b",
        "text_fg": "#e0e0e0",
        "button_bg": "#3c3c3c",
        "button_active": "#4a4a4a",
        "border": "#555555",
        "select_bg": "#264f78",
        "error": "#ef5350",
        "success": "#66bb6a",
    },
}


class BinaryCodeReaderApp(_TkBase):
    def __init__(self, config_dir: Path | None = None) -> None:
        super().__init__()
        self.title("Binary Code Reader")
        self.geometry("900x560")
        self.minsize(700, 420)

        # Where settings and history live (a custom folder is handy for experiments)
        folder = Path(config_dir) if config_dir else default_config_dir()
        self._settings_path = folder / "settings.json"
        self._history_path = folder / "history.json"
        self._settings = load_settings(self._settings_path)

        self.theme_name = self._settings["theme"]
        self._status_kind: str | None = None  # None, "success" or "error"

        self.history = History()
        self._shown_entries: list[HistoryEntry] = []  # what the Listbox shows

        self._build_widgets()
        self._apply_theme()

        if self._settings["remember_history"]:
            self.history.load(self._history_path)
            self._refresh_history()

        if not DND_AVAILABLE:
            self.status.config(
                text="Ready. (Drag & Drop disabled: pip install tkinterdnd2)"
            )

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    # ---------- Layout ----------

    def _build_widgets(self) -> None:
        outer = ttk.Frame(self, padding=12)
        outer.pack(fill="both", expand=True)
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(0, weight=1)

        # Left side: the converter
        container = ttk.Frame(outer)
        container.grid(row=0, column=0, sticky="nsew")

        # Right side: history panel
        self._build_history_panel(outer)

        # One column that stretches; the two text areas share the extra height
        container.columnconfigure(0, weight=1)
        container.rowconfigure(1, weight=1)
        container.rowconfigure(4, weight=1)

        # Row 0: "Input" label, encoding selector, theme toggle
        header = ttk.Frame(container)
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)

        input_label = "Input (drop a .txt file here)" if DND_AVAILABLE else "Input"
        ttk.Label(header, text=input_label).grid(row=0, column=0, sticky="w")
        ttk.Label(header, text="Encoding:").grid(row=0, column=1, padx=(0, 4))
        self.encoding_var = tk.StringVar(value=self._settings["encoding"])
        self.encoding_combo = ttk.Combobox(
            header,
            textvariable=self.encoding_var,
            values=SUPPORTED_ENCODINGS,
            state="readonly",
            width=10,
        )
        self.encoding_combo.grid(row=0, column=2)
        self.theme_button = ttk.Button(
            header, text="☾ Dark", width=8, command=self.on_toggle_theme
        )
        self.theme_button.grid(row=0, column=3, padx=(8, 0))

        # Row 1: input box
        self.input_box = scrolledtext.ScrolledText(
            container, height=8, wrap="word", font=("Consolas", 11)
        )
        self.input_box.grid(row=1, column=0, sticky="nsew", pady=(4, 8))
        if DND_AVAILABLE:
            self.input_box.drop_target_register(DND_FILES)
            self.input_box.dnd_bind("<<Drop>>", self.on_drop)

        # Row 2: conversion buttons
        convert_row = ttk.Frame(container)
        convert_row.grid(row=2, column=0, pady=4)
        ttk.Button(
            convert_row, text="Auto ✨", command=self.on_auto_convert
        ).pack(side="left", padx=4)
        ttk.Button(
            convert_row, text="Text → Binary", command=self.on_text_to_binary
        ).pack(side="left", padx=4)
        ttk.Button(
            convert_row, text="Binary → Text", command=self.on_binary_to_text
        ).pack(side="left", padx=4)

        # Row 3-4: output (read-only)
        ttk.Label(container, text="Output").grid(row=3, column=0, sticky="w")
        self.output_box = scrolledtext.ScrolledText(
            container, height=8, wrap="word", font=("Consolas", 11), state="disabled"
        )
        self.output_box.grid(row=4, column=0, sticky="nsew", pady=(4, 8))

        # Row 5: utility buttons
        util_row = ttk.Frame(container)
        util_row.grid(row=5, column=0, pady=4)
        ttk.Button(util_row, text="Copy", command=self.on_copy).pack(side="left", padx=4)
        ttk.Button(util_row, text="Paste", command=self.on_paste).pack(side="left", padx=4)
        ttk.Button(util_row, text="Clear", command=self.on_clear).pack(side="left", padx=4)
        ttk.Button(util_row, text="Open file…", command=self.on_open_file).pack(
            side="left", padx=(16, 4)
        )
        ttk.Button(util_row, text="Save output…", command=self.on_save_output).pack(
            side="left", padx=4
        )

        # Row 6: status line
        self.status = ttk.Label(container, text="Ready.")
        self.status.grid(row=6, column=0, sticky="w", pady=(8, 0))

    def _build_history_panel(self, parent: ttk.Frame) -> None:
        panel = ttk.Frame(parent)
        panel.grid(row=0, column=1, sticky="ns", padx=(12, 0))
        panel.rowconfigure(1, weight=1)

        ttk.Label(panel, text="History (double-click to restore)").grid(
            row=0, column=0, columnspan=2, sticky="w"
        )

        self.history_list = tk.Listbox(
            panel,
            width=34,
            activestyle="none",
            exportselection=False,
            font=("Consolas", 10),
        )
        self.history_list.grid(row=1, column=0, sticky="ns", pady=(4, 8))
        scroll = ttk.Scrollbar(panel, command=self.history_list.yview)
        scroll.grid(row=1, column=1, sticky="ns", pady=(4, 8))
        self.history_list.config(yscrollcommand=scroll.set)
        self.history_list.bind("<Double-Button-1>", self.on_history_restore)

        ttk.Button(
            panel, text="Clear history", command=self.on_clear_history
        ).grid(row=2, column=0, columnspan=2)

        self.remember_var = tk.BooleanVar(value=self._settings["remember_history"])
        ttk.Checkbutton(
            panel,
            text="Remember history",
            variable=self.remember_var,
            command=self.on_toggle_remember,
        ).grid(row=3, column=0, columnspan=2, sticky="w", pady=(8, 0))

    # ---------- Theme ----------

    def _apply_theme(self) -> None:
        """Paint every widget with the current palette."""
        p = THEMES[self.theme_name]
        self.configure(background=p["bg"])

        # ttk widgets: styled centrally through ttk.Style
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(".", background=p["bg"], foreground=p["fg"])
        style.configure("TFrame", background=p["bg"])
        style.configure("TLabel", background=p["bg"], foreground=p["fg"])
        style.configure("TCheckbutton", background=p["bg"], foreground=p["fg"])
        style.map("TCheckbutton", background=[("active", p["bg"])])
        style.configure(
            "TButton",
            background=p["button_bg"],
            foreground=p["fg"],
            bordercolor=p["border"],
            focuscolor=p["button_bg"],
        )
        style.map("TButton", background=[("active", p["button_active"])])
        style.configure(
            "TCombobox",
            fieldbackground=p["text_bg"],
            background=p["button_bg"],
            foreground=p["text_fg"],
            arrowcolor=p["fg"],
            bordercolor=p["border"],
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", p["text_bg"])],
            foreground=[("readonly", p["text_fg"])],
            selectbackground=[("readonly", p["text_bg"])],
            selectforeground=[("readonly", p["text_fg"])],
        )

        # Classic tk widgets: each one is configured by hand
        for box in (self.input_box, self.output_box):
            box.config(
                background=p["text_bg"],
                foreground=p["text_fg"],
                insertbackground=p["text_fg"],  # the blinking cursor
                selectbackground=p["select_bg"],
                selectforeground=p["text_fg"],
            )

        self.history_list.config(
            background=p["text_bg"],
            foreground=p["text_fg"],
            selectbackground=p["select_bg"],
            selectforeground=p["text_fg"],
            highlightbackground=p["border"],
            highlightcolor=p["border"],
        )

        self._style_combobox_popup(p)

        # The button shows the mode you will switch TO
        self.theme_button.config(
            text="☀ Light" if self.theme_name == "dark" else "☾ Dark"
        )
        self._paint_status()

    def _style_combobox_popup(self, palette: dict[str, str]) -> None:
        """Color the dropdown list of the Combobox (it is a separate window)."""
        try:
            popdown = self.tk.eval(
                f"ttk::combobox::PopdownWindow {self.encoding_combo}"
            )
            self.tk.call(
                f"{popdown}.f.l",
                "configure",
                "-background", palette["text_bg"],
                "-foreground", palette["text_fg"],
                "-selectbackground", palette["select_bg"],
                "-selectforeground", palette["text_fg"],
            )
        except tk.TclError:
            pass  # purely cosmetic: never let it break the app

    def _paint_status(self) -> None:
        p = THEMES[self.theme_name]
        color = {
            "error": p["error"],
            "success": p["success"],
        }.get(self._status_kind, p["fg"])
        self.status.config(foreground=color)

    # ---------- Helpers ----------

    def _set_output(self, text: str) -> None:
        # A disabled Text widget ignores inserts, so unlock it briefly
        self.output_box.config(state="normal")
        self.output_box.delete("1.0", "end")
        self.output_box.insert("1.0", text)
        self.output_box.config(state="disabled")

    def _show_status(self, message: str, is_error: bool) -> None:
        self._status_kind = "error" if is_error else "success"
        self.status.config(text=message)
        self._paint_status()

    def _convert(self, mode: str) -> None:
        convert_func = text_to_binary if mode == "text_to_binary" else binary_to_text
        # "end-1c" = everything except the extra newline Tk adds at the end
        source = self.input_box.get("1.0", "end-1c")
        encoding = self.encoding_var.get()
        try:
            result = convert_func(source, encoding)
        except ValueError as error:
            self._set_output("")
            self._show_status(str(error), is_error=True)
            return
        self._set_output(result)
        self._record(mode, encoding, source, result)
        self._show_status("Conversion successful.", is_error=False)

    def _record(self, mode: str, encoding: str, source: str, result: str) -> None:
        if len(source) > HISTORY_MAX_SOURCE:
            return  # too big to keep 50 of them in memory
        if self.history.add(mode, encoding, source, result):
            self._refresh_history()

    def _refresh_history(self) -> None:
        self._shown_entries = self.history.entries_newest_first()
        self.history_list.delete(0, "end")
        for entry in self._shown_entries:
            self.history_list.insert("end", entry.preview())

    def _load_file(self, path: str) -> None:
        """Read a file into the input box (shared by Open and Drop)."""
        try:
            text = read_text_file(path, self.encoding_var.get())
        except ValueError as error:
            self._show_status(str(error), is_error=True)
            return
        self.input_box.delete("1.0", "end")
        self.input_box.insert("1.0", text)
        name = os.path.basename(path)
        self._show_status(f"Loaded {name} ({len(text):,} characters).", is_error=False)

    # ---------- Button callbacks ----------

    def on_text_to_binary(self) -> None:
        self._convert("text_to_binary")

    def on_binary_to_text(self) -> None:
        self._convert("binary_to_text")

    def on_auto_convert(self) -> None:
        source = self.input_box.get("1.0", "end-1c")
        encoding = self.encoding_var.get()
        try:
            mode, result = auto_convert(source, encoding)
        except ValueError as error:
            self._set_output("")
            self._show_status(str(error), is_error=True)
            return

        self._set_output(result)
        self._record(mode, encoding, source, result)
        label = "Binary → Text" if mode == "binary_to_text" else "Text → Binary"
        self._show_status(f"Auto-detected: {label}", is_error=False)

    def on_copy(self) -> None:
        text = self.output_box.get("1.0", "end-1c")
        if not text:
            self._show_status("Nothing to copy.", is_error=True)
            return
        self.clipboard_clear()
        self.clipboard_append(text)
        self._show_status("Copied to clipboard.", is_error=False)

    def on_paste(self) -> None:
        try:
            text = self.clipboard_get()
        except tk.TclError:
            self._show_status("Clipboard is empty or not text.", is_error=True)
            return
        self.input_box.delete("1.0", "end")
        self.input_box.insert("1.0", text)
        self._show_status("Pasted from clipboard.", is_error=False)

    def on_clear(self) -> None:
        self.input_box.delete("1.0", "end")
        self._set_output("")
        self.status.config(text="Ready.")
        self._status_kind = None
        self._paint_status()

    def on_toggle_theme(self) -> None:
        self.theme_name = "dark" if self.theme_name == "light" else "light"
        self._apply_theme()

    def on_open_file(self) -> None:
        path = filedialog.askopenfilename(
            title="Open text file",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if path:  # an empty string means the user cancelled
            self._load_file(path)

    def on_save_output(self) -> None:
        text = self.output_box.get("1.0", "end-1c")
        if not text:
            self._show_status("Nothing to save.", is_error=True)
            return
        path = filedialog.asksaveasfilename(
            title="Save output",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            write_text_file(path, text)
        except ValueError as error:
            self._show_status(str(error), is_error=True)
            return
        self._show_status(f"Saved to {os.path.basename(path)}.", is_error=False)

    def on_drop(self, event: tk.Event) -> None:
        # event.data looks like "{C:/my folder/a.txt} C:/b.txt"; splitlist parses it
        paths = self.tk.splitlist(event.data)
        if not paths:
            return
        self._load_file(paths[0])
        if len(paths) > 1 and self._status_kind == "success":
            self._show_status(
                f"Loaded only the first of {len(paths)} files.", is_error=False
            )

    def on_history_restore(self, _event: tk.Event) -> None:
        selection = self.history_list.curselection()
        if not selection:
            return
        entry = self._shown_entries[selection[0]]
        self.input_box.delete("1.0", "end")
        self.input_box.insert("1.0", entry.source)
        self.encoding_var.set(entry.encoding)
        self._set_output(entry.result)
        self._show_status("Restored from history.", is_error=False)

    def on_clear_history(self) -> None:
        self.history.clear()
        self._refresh_history()
        self._show_status("History cleared.", is_error=False)

    def on_toggle_remember(self) -> None:
        if self.remember_var.get():
            self._show_status(
                "History will be saved when you close the app.", is_error=False
            )
            return
        # Unchecked: the user expects nothing to stay on disk, so delete it now
        try:
            remove_file(self._history_path)
        except ValueError as error:
            self._show_status(str(error), is_error=True)
            return
        self._show_status("History will not be saved (saved file deleted).", is_error=False)

    def on_close(self) -> None:
        remember = self.remember_var.get()
        self._settings.update(
            theme=self.theme_name,
            encoding=self.encoding_var.get(),
            remember_history=remember,
        )
        try:
            save_settings(self._settings_path, self._settings)
            if remember:
                self.history.save(self._history_path)
            else:
                remove_file(self._history_path)
        except ValueError as error:
            # The window is closing, so there is nowhere to show this: log it
            print(f"Warning: {error}", file=sys.stderr)
        self.destroy()


def run(config_dir: Path | None = None) -> None:
    app = BinaryCodeReaderApp(config_dir)
    app.mainloop()