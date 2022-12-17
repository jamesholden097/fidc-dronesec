import time
import tkinter
import numpy as np
import customtkinter
from multiprocessing import Process
from typing import Union, Callable, Any

# implement yes no choice window with default return value stuff


class FloatSpinbox(customtkinter.CTkFrame):
    def __init__(self, *args,
                 width: int = 100,
                 height: int = 32,
                 text: str = "CTkFloatSpinbox",
                 default_value: float = 0.0,
                 step_size: Union[int, float] = 1,
                 command: Callable = None,
                 **kwargs):
        super().__init__(*args, width=width, height=height, **kwargs)

        self.text = text
        self.step_size = step_size
        self.command = command

        self.grid_columnconfigure((0, 2), weight=0)  # buttons don't expand
        self.grid_columnconfigure(1, weight=1)  # entry expands

        self.label = customtkinter.CTkLabel(self, text=self.text)
        self.label.grid(row=0, column=1, sticky="nsew")

        self.subtract_button = customtkinter.CTkButton(
            self,
            text="-",
            width=height - 6,
            height=height - 6,
            command=self.subtract_button_callback)
        self.subtract_button.grid(row=1, column=0, padx=(3, 0), pady=3)

        self.entry = customtkinter.CTkEntry(
            self, width=width - (2 * height), height=height - 6, justify="right")
        self.entry.grid(row=1, column=1, columnspan=1, padx=3, pady=3, sticky="ew")
        self.entry.bind("<Return>", self.set_val)

        self.add_button = customtkinter.CTkButton(
            self,
            text="+",
            width=height - 6,
            height=height - 6,
            command=self.add_button_callback)
        self.add_button.grid(row=1, column=2, padx=(0, 3), pady=3)

        # default value
        self.entry.insert(0, str(default_value))

    def add_button_callback(self):
        try:
            value = float(self.entry.get()) + self.step_size
            self.entry.delete(0, "end")
            self.entry.insert(0, value)
        except ValueError:
            return
        if self.command is not None:
            self.command()

    def subtract_button_callback(self):

        try:
            value = float(self.entry.get()) - self.step_size
            self.entry.delete(0, "end")
            self.entry.insert(0, value)
        except ValueError:
            return
        if self.command is not None:
            self.command()

    def get(self) -> Union[float, None]:
        try:
            return float(self.entry.get())
        except ValueError:
            return None

    def set(self, value: float):
        self.entry.delete(0, "end")
        self.entry.insert(0, str(float(value)))

    def set_val(self, arg):
        self.set(self.get())
        if self.command is not None:
            self.command()


class CTkDictInput:
    def __init__(self,
                 master=None,
                 icon=None,
                 title="CTkDictInput",
                 text="CTkDictInput",
                 dictionary={}):
        self.title = title

        self.text = text
        self.dictionary = dictionary

        self.top = customtkinter.CTkToplevel()
        self.top.title(self.title)
        if icon:
            self.icon = icon
            self.top.iconbitmap(self.icon)
        self.spinboxes = []

        self.top.lift()
        self.top.focus_force()
        self.top.grab_set()
        self.top.protocol("WM_DELETE_WINDOW", self.on_closing)
        # create widgets with slight delay, to avoid white flickering of background
        self.top.after(10, self.create_widgets)
        self.run()

    def create_widgets(self):

        self.frame_top = customtkinter.CTkFrame(master=self.top)
        self.frame_top.grid(
            row=0, column=0, sticky="nsew", padx=(
                10, 10), pady=(
                10, 10))
        dict_length = len(self.dictionary)
        rows = int(np.ceil(np.sqrt(dict_length)))
        cols = int(np.ceil(dict_length / rows))
        keys = list(self.dictionary.keys())

        for i in range(rows):
            for j in range(cols):
                if cols * i + j <= dict_length - 1:
                    self.spinboxes.append(FloatSpinbox(master=self.frame_top,
                                                       text=keys[cols * i + j],
                                                       step_size=1.0,
                                                       default_value=self.dictionary[keys[cols * i + j]],
                                                       command=lambda text=keys[cols * i + j]: self.spinbox_callback(text,
                                                                                                                     self.dictionary)))
                    self.spinboxes[-1].grid(row=i + 1, column=j,
                                            padx=(10, 10), pady=(10, 10), sticky="nsew")

        self.label_top = customtkinter.CTkLabel(master=self.frame_top, text=self.text)
        self.label_top.grid(
            row=0, column=0, columnspan=rows, padx=(
                10, 10), pady=(
                10, 10), sticky="nsew")

        self.frame_bottom = customtkinter.CTkFrame(master=self.top)
        self.frame_bottom.grid(
            row=1, column=0, columnspan=rows, sticky="ew", padx=(
                10, 10), pady=(
                10, 10))
        self.frame_bottom.grid_columnconfigure(0, weight=1)
        self.frame_bottom.grid_columnconfigure(1, weight=1)
        self.label_bottom = customtkinter.CTkLabel(
            master=self.frame_bottom, text=f" Confirm {self.text}")
        self.label_bottom.grid(
            row=0, column=0, columnspan=rows, padx=(
                10, 10), pady=(
                10, 10), sticky="ew")

        self.ok_button = customtkinter.CTkButton(
            master=self.frame_bottom, text='Ok', width=100, command=self.ok_event)
        self.ok_button.grid(
            row=rows + 1,
            column=0,
            padx=(
                10,
                10),
            pady=(
                10,
                10),
            sticky="ew")

        self.cancel_button = customtkinter.CTkButton(
            master=self.frame_bottom, text='Cancel', width=100, command=self.cancel_event)
        self.cancel_button.grid(
            row=rows + 1,
            column=1,
            padx=(
                10,
                10),
            pady=(
                10,
                10),
            sticky="ew")
        self.top.resizable(0, 0)

    def spinbox_callback(self, *args):
        for spinbox in self.spinboxes:
            if args[0] == spinbox.text:
                args[1][args[0]] = spinbox.get()
        #print(f"{args[0]} : {args[1][args[0]]}")

    def confirm_event(self):
        # implement yes no choice window
        return True

    def ok_event(self, event=None):
        if self.confirm_event():
            self.running = False

    def on_closing(self):
        if self.confirm_event():
            self.running = False

    def cancel_event(self):
        if self.confirm_event():
            self.running = False

    def run(self):
        self.running = True

        while self.running:
            try:
                self.top.update()
            except Exception:
                return self.dictionary
            finally:
                time.sleep(0.01)

        time.sleep(0.05)
        self.top.destroy()

    def get_value(self):
        return self.dictionary


class CTkMessageBox:
    def __init__(self,
                 master=None,
                 icon=None,
                 title="CTkMessageBox",
                 message="CTkMessageBox",
                 ):
        self.title = title
        self.message = message

        self.top = customtkinter.CTkToplevel()
        self.top.title(self.title)

        if icon:
            self.icon = icon
            self.top.iconbitmap(self.icon)

        self.top.grid_columnconfigure(0, weight=1)
        self.top.grid_rowconfigure(0, weight=1)
        self.top.lift()
        self.top.focus_force()
        self.top.grab_set()
        self.top.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.top.after(10, self.create_widgets)

        self.run()

    def create_widgets(self):
        self.label = customtkinter.CTkLabel(
            self.top, text=f"{self.title}    :    {self.message}        ")
        self.label.grid(row=0, column=0, padx=(10, 10), pady=(10, 10), sticky="nsew")

        self.button = customtkinter.CTkButton(
            self.top, text="  OK  ", command=self.ok_event)
        self.button.grid(row=1, column=0, padx=(10, 10), pady=(10, 10), sticky="nsew")
        self.top.resizable(0, 0)

    def confirm_event(self):
        # implement yes no choice window
        return True

    def ok_event(self, event=None):
        if self.confirm_event():
            self.running = False

    def on_closing(self):
        if self.confirm_event():
            self.running = False

    def run(self):
        self.running = True

        while self.running:
            try:
                self.top.update()
            except Exception:
                return self.dictionary
            finally:
                time.sleep(0.01)

        time.sleep(0.05)
        self.top.destroy()


if __name__ == "__main__":
    print(__file__)
