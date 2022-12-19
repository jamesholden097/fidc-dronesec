import os
import csv
import sys
import time
import random
import tkinter
import navpy as nv
import numpy as np
import customtkinter
from typing import Any
from queue import Queue
import tkinter.filedialog
from threading import Thread
from colony.swarm import Swarm
from PIL import Image, ImageTk
from colony.datatype import Matrix
from tkintermapview import TkinterMapView
from multiprocessing import Process, Manager
from app_util import CTkDictInput, CTkMessageBox

customtkinter.set_appearance_mode("Dark")
customtkinter.set_default_color_theme("dark-blue")

class App(customtkinter.CTk):
    WIDTH = 1200
    HEIGHT = 800

    def __init__(self):

        super().__init__()

        self.title("SkySentinel")
        self.geometry(f"{App.WIDTH}x{App.HEIGHT}")
        self.minsize(App.WIDTH, App.HEIGHT)
        self.resizable(True, True)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)


        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)

        self.frame_left = customtkinter.CTkFrame(master=self)
        self.frame_left.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.frame_left.grid_columnconfigure(0, weight=0)
        self.frame_left.grid_columnconfigure(1, weight=0)

        self.frame_right_top = customtkinter.CTkFrame(master=self)
        self.frame_right_top.grid(row=0, column=1, sticky="nsew")
        self.frame_right_top.grid_rowconfigure(0, weight=1)
        self.frame_right_top.grid_columnconfigure(0, weight=1)

        self.frame_right_bottom = customtkinter.CTkFrame(master=self)
        self.frame_right_bottom.grid(row=1, column=1, sticky="sew")
        self.frame_right_bottom.grid_rowconfigure(0, weight=1)
        self.frame_right_bottom.grid_columnconfigure(0, weight=1)

        self.logs = str()
        self.threads = []
        self.buttons = {}
        self.drone_markers = []
        self.map_markers = []
        self.reference_marker = None
        self.drone_paths = []

        self.connection_strings = None
        self.filetypes = (("text files", "*.txt"), ("All files", "*.*"))
        self.swarm = None
        self.local_reference = None
        self.monitor_position = False
        self.constraints = {
            'take_off_alt' : 5.0
        }
        self.hold = True
        self.position_q = Queue()

        self.add_widgets()

    def add_widgets(self):

        # Frame Right Bottom
        # integrate logging module

        self.tk_textbox = tkinter.Text(master=self.frame_right_bottom, highlightthickness=0, state='disabled', height=6, padx=5, pady=5)
        self.tk_textbox.grid(row=0, column=0, padx=(5, 5), pady=(5, 5), sticky="we")
        self.tk_textbox.configure(font=('monserat', 8))
        self.tk_textbox.tag_config('INFO', foreground='black')
        self.tk_textbox.tag_config('DEBUG', foreground='gray')
        self.tk_textbox.tag_config('WARNING', foreground='orange')
        self.tk_textbox.tag_config('ERROR', foreground='red')
        self.tk_textbox.tag_config('CRITICAL', foreground='red', underline=1)

        self.ctk_textbox_scrollbar = customtkinter.CTkScrollbar(
            master=self.frame_right_bottom, command=self.tk_textbox.yview, height=6)
        self.ctk_textbox_scrollbar.grid(row=0, column=1, padx=(5, 5), pady=(5, 5), sticky="ns")
        self.tk_textbox.configure(yscrollcommand=self.ctk_textbox_scrollbar.set)

        # Frame right top
        self.map_widget = TkinterMapView(master=self.frame_right_top, corner_radius=10)
        self.map_widget.set_tile_server("https://mt0.google.com/vt/lyrs=m&hl=en&x={x}&y={y}&z={z}&s=Ga", max_zoom=22)
        self.map_widget.grid(row=0, column=0, columnspan=4, sticky="nswe", padx=(5, 5), pady=(5, 5))
        self.map_widget.set_address("Uttara, Dhaka")

        self.map_widget.add_right_click_menu_command(label="Place Marker", command=self.right_click_event, pass_coords=True)
        self.map_widget.add_right_click_menu_command(label="Set Reference Location", command=self.set_lla_ref, pass_coords=True)

        self.search_entry = customtkinter.CTkEntry(master=self.frame_right_top, placeholder_text="Search Address")
        self.search_entry.grid(row=1, column=0, sticky="we", padx=(5, 5), pady=(5, 5))
        self.search_entry.bind("<Return>", self.search_event)

        # add post req status if search was successful or not
        self.search_button = customtkinter.CTkButton(master=self.frame_right_top, text="Search", width=90, command=self.search_event)
        self.search_button.grid(row=1, column=1, sticky="w", padx=(5, 5), pady=(5, 5))

        self.clear_marker_button = customtkinter.CTkButton(master=self.frame_right_top, text="Clear Markers", command=self.clear_marker_event)
        self.clear_marker_button.grid(row=1, column=2, sticky="w", pady=(5, 5), padx=(5, 5))
        self.map_list = ["Google normal", "Google satellite", "OpenStreetMap", "PaintMap", "B&WMap", "HikeMap", "Map", "TopologicalMap", "SeaMap", "RailWayMap"]
        self.map_option_menu = customtkinter.CTkOptionMenu(master=self.frame_right_top, values=self.map_list, command=self.change_map)
        self.map_option_menu.grid(row=1, column=3, padx=(5, 5), pady=(5, 5), sticky="e")
        self.map_option_menu.set("Google normal")

        # Frame Left

        self.create_button(self.frame_left, text="Connection List", row=0, column=0, sticky="w")

        self.create_button(self.frame_left, text="Connect", row=0, column=1, sticky="w")
        self.connection_progressbar = customtkinter.CTkProgressBar(master=self.frame_left, mode="determinate")
        self.connection_progressbar.grid(row=1, column=0, columnspan=2, padx=(5, 5), pady=(5, 5), sticky="wes")
        self.connection_progressbar.stop()
        self.connection_progressbar.set(0.)
        self.tgt_drone_label = customtkinter.CTkLabel(self.frame_left, text=f"Target Vehicle : \nNONE")
        self.tgt_drone_label.grid(row=2, column=0, columnspan=2, padx=(5, 5), pady=(5, 5), sticky="we")

        self.connectionlist_optionmenu = customtkinter.CTkOptionMenu(master=self.frame_left, values=['NONE'], command=self.connectionlist_optionmenu_callback)

        self.connectionlist_optionmenu.grid(row=3, column=0, padx=(5, 5), pady=(5, 5), sticky="we")

        self.switch = customtkinter.CTkSwitch(master=self.frame_left, text="Select all",
                                              command=self.switch_event, onvalue="on", offvalue="off")
        self.switch.grid(row=3, column=1, padx=(5, 5), pady=(5, 5), sticky="e")
        self.switch.select()

        # set from dronekit or pymavlnk util idk
        action_list = [f"Action {i + 1}" for i in range(10)]
        self.action_list_optionmenu = customtkinter.CTkOptionMenu(
            master=self.frame_left, values=action_list, command=self.action_list_optionmenu_callback)
        self.action_list_optionmenu.grid(row=4, column=0, padx=(5, 5), pady=(5, 5), sticky="w")

        self.create_button(self.frame_left, text="Do Action", row=4, column=1, sticky="w")

        # mode_list = [ f"Mode {i + 1}" for i in range(10)] # set from arducopter
        # firmwire page
        mode_list = ["STABILIZE", "ALT_HOLD", "LOITER", "SMART_RTL", "RTL", "LAND", "GUIDED", "AUTO", "ACRO"]  # set from arducopter frimwire page

        self.mode_list_optionmenu = customtkinter.CTkOptionMenu(
            master=self.frame_left, values=mode_list, command=self.mode_list_optionmenu_callback)

        self.mode_list_optionmenu.grid(row=5, column=0, padx=(5, 5), pady=(5, 5), sticky="w")

        self.create_button(self.frame_left, text="Set Mode", row=5, column=1, sticky="w")

        self.create_button(self.frame_left, text="ARM", row=6, column=0, sticky="w")

        self.create_button(self.frame_left, text="DISARM", row=6, column=1, sticky="w")

        self.create_button(self.frame_left, text="Takeoff", row=7, column=0, sticky="w")

        self.create_button(self.frame_left, text="LAND", row=7, column=1, sticky="w")

        self.create_button(self.frame_left, text="sRTL", row=8, column=0, sticky="w")

        self.create_button(self.frame_left, text="RTL", row=8, column=1, sticky="w")

        self.create_button(self.frame_left, text="Hold", row=9, column=0, columnspan=2, sticky="we")


        self.create_button(self.frame_left, text="Goto Marker", row=10, column=0, columnspan=2, sticky="we")


        self.create_button(self.frame_left, text="Disconnect All", row=11, column=0, columnspan=2, sticky="we")

        self.appearance_mode_label = customtkinter.CTkLabel(self.frame_left, text=" Appearance Mode: ")
        self.appearance_mode_label.grid(row=12, column=0, columnspan=2, padx=(5, 5), pady=(5, 5), sticky="wes")

        self.appearance_mode_optionemenu = customtkinter.CTkOptionMenu(
            master=self.frame_left, values=[ "System", "Light", "Dark"], command=self.change_appearance_mode)
        self.appearance_mode_optionemenu.grid(row=13, column=0, columnspan=2, padx=(5, 5), pady=(5, 5), sticky="wes")

    def debug_print(self, data):
        data = f"{time.time()} : {data}"
        self.logs += data + '\n'
        self.tk_textbox.configure(state='normal')
        self.tk_textbox.insert(tkinter.END, data + '\n')
        self.tk_textbox.configure(state='disabled')
        # Autoscroll to the bottom
        self.tk_textbox.yview(tkinter.END)
        # print(data)

    def right_click_event(self, coordinates_tuple):
        self.debug_print(f"Right click event with coordinates: {coordinates_tuple}")
        marker_dialog = customtkinter.CTkInputDialog(text=f"Enter Height : ", title="    Height Input    ")
        marker_height = marker_dialog.get_input() or self.constraints['take_off_alt']
        self.map_markers.append(self.map_widget.set_marker(coordinates_tuple[0], coordinates_tuple[1], text=f'{marker_height} m.'))

        height = float(marker_height) if  self.is_float(marker_height) else self.constraints['take_off_alt'] + 10.0
        position = np.asarray([coordinates_tuple[0], coordinates_tuple[1], height])
        self.position_q.put(position)
        self.debug_print(list(self.position_q.queue))

    def set_lla_ref(self, coordinates):
        if self.reference_marker is not None:
            self.reference_marker.delete()
        self.reference_marker = self.map_widget.set_marker(coordinates[0], coordinates[1], text="Reference")
        self.local_reference = np.asarray([coordinates[0], coordinates[1], 0])
        self.debug_print(f"Local Reference set at : {self.local_reference}")

    def search_event(self, event=None):
        self.map_widget.set_address(self.search_entry.get())

    def clear_marker_event(self):
        for marker in self.map_markers:
            marker.delete()
        self.reference_marker.delete() if self.reference_marker is not None else self.debug_print("Reference not set")
        with self.position_q.mutex:
            self.position_q.queue.clear()

    def change_map(self, new_map: str):
        if new_map == "Google normal":
            self.map_widget.set_tile_server(
                "https://mt0.google.com/vt/lyrs=m&hl=en&x={x}&y={y}&z={z}&s=Ga", max_zoom=22)
        elif new_map == "Google satellite":
            self.map_widget.set_tile_server(
                "https://mt0.google.com/vt/lyrs=s&hl=en&x={x}&y={y}&z={z}&s=Ga", max_zoom=22)
        elif new_map == "OpenStreetMap":
            self.map_widget.set_tile_server("https://a.tile.openstreetmap.org/{z}/{x}/{y}.png")
        elif new_map == "PaintMap":
            self.map_widget.set_tile_server("http://c.tile.stamen.com/watercolor/{z}/{x}/{y}.png")  # painting style
        elif new_map == "B&WMap":
            self.map_widget.set_tile_server("http://a.tile.stamen.com/toner/{z}/{x}/{y}.png")  # black and white
        elif new_map == "HikeMap":
            self.map_widget.set_tile_server("https://tiles.wmflabs.org/hikebike/{z}/{x}/{y}.png")  # detailed hiking
        elif new_map == "Map":
            self.map_widget.set_tile_server("https://tiles.wmflabs.org/osm-no-labels/{z}/{x}/{y}.png")  # no labels
        elif new_map == "TopologicalMap":
            self.map_widget.set_tile_server(
                "https://wmts.geo.admin.ch/1.0.0/ch.swisstopo.pixelkarte-farbe/default/current/3857/{z}/{x}/{y}.jpeg")  # swisstopo map

            # example overlay tile server
        elif new_map == "SeaMap":
            self.map_widget.set_overlay_tile_server("http://tiles.openseamap.org/seamark//{z}/{x}/{y}.png")  # sea-map overlay
        elif new_map == "RailWayMap":
            self.map_widget.set_overlay_tile_server("http://a.tiles.openrailwaymap.org/standard/{z}/{x}/{y}.png")  # railway infrastructure

    def create_button(self, frame, text, row, column, rowspan=1, columnspan=1, sticky=""):
        self.buttons[text] = customtkinter.CTkButton(master=frame, text=text, command=lambda text=text: self.button_callback(text))
        self.buttons[text].grid(row=row, column=column, rowspan=rowspan, columnspan=columnspan, padx=(5, 5), pady=(5, 5), sticky=sticky)

    def button_callback(self, button_name):
        self.debug_print(f"Button Pressed : {button_name}")

        if button_name == "Connection List":
            if self.connection_strings  and self.swarm:
                CTkMessageBox(title='Error', message="Connection String Not Empty. \nDisconnect First.")
                return

            else:
                self.filename = tkinter.filedialog.askopenfilename(
                    title='Open Connection List', initialdir=os.getcwd(), filetypes=self.filetypes)
                self.connection_strings = self.read_file(self.filename)  
                if self.connection_strings:
                    CTkMessageBox(title='Connection List', message=f"Filename : {self.filename} \n Connection List : {(self.connection_strings)}")
                    connection_list_option = self.connection_strings if self.switch.get() == "off" else [f"ALL"]
                    self.connectionlist_optionmenu.configure(values=connection_list_option)
                    self.connectionlist_optionmenu.set(connection_list_option[0])
                    self.tgt_drone_label.configure(text=f"Target Vehicle : \n{connection_list_option[0]}")
                    self.debug_print(f"connection string : {self.connection_strings}")

                else:
                    self.debug_print(f"FileNotFoundError")
                    CTkMessageBox(title='FileNotFoundError', message="Can't find file")
                return

        if button_name == 'Connect':

            if self.connection_strings is None:
                CTkMessageBox(title='Error', message="Connection String Empty.")

            if self.local_reference is None:
                CTkMessageBox(title='Error', message="Local Reference Not Set.")

            if self.swarm is not None:
                CTkMessageBox(title='Error', message="Swarm already Connected.")

            if self.connection_strings is not None and self.local_reference is not None and self.swarm is None:
                try:
                    self.connect_swarm()
                    self.debug_print("Connection Thread Started.")
                    self.monitor_position = True

                    self.position_monitor_thread = Thread(target=self.position_monitor, daemon=False)
                    self.threads.append(self.position_monitor_thread)
                    self.position_monitor_thread.start()
                    self.debug_print("Position Monitor Thread Started.")
                    return

                except Exception as e:
                    self.debug_print(f"Exception : {e}")
                    return

        if self.swarm:
            if button_name == "Set Mode":
                self.set_mode(self.mode_list_optionmenu.get())
                return

            if button_name == "ARM":
                self.set_state("ARM")
                return

            if button_name == "DISARM":
                self.set_state("DISARM")
                return

            if button_name == "Takeoff":

                dialog = customtkinter.CTkInputDialog(text=f"Takeoff alt (m) : \n Deafault {self.constraints['take_off_alt']} m", title="Enter Takeoff Height in meters")
                user_input = dialog.get_input()
                alt = float(user_input) if self.is_float(user_input) else self.constraints['take_off_alt']
                self.take_off_thread = Thread(target=self.takeoff, args=(alt,), daemon=False)
                self.threads.append(self.take_off_thread)
                self.take_off_thread.start()
                self.debug_print(f"Takeoff Thread started.")

                return

            if button_name == "LAND":
                self.set_mode("LAND")
                return

            if button_name == "RTL":
                self.set_mode("RTL")
                return

            if button_name == "sRTL":
                self.set_mode("SMART_RTL")
                return

            if button_name == "Hold":
                self.hold = not self.hold
                pass


            if button_name == "Goto Marker":
                self.goto_thread = Thread(target=self.goto_marker, daemon=False)
                self.goto_thread.start()
                self.threads.append(self.goto_thread)

            if button_name == "Disconnect All":

                self.disconnect_swarm()
                return

        else:
            CTkMessageBox(title='Error', message="Swarm Not Connected")

    def connectionlist_optionmenu_callback(self, choice):
        self.debug_print(f"optionmenu dropdown clicked: {choice}")
        self.tgt_drone_label.configure(text=f"Target Vehicle : \n{choice}")

    def switch_event(self):
        self.debug_print(f"switch  value: {self.switch.get()}")

        if self.connection_strings:
            connection_list_option = self.connection_strings if self.switch.get() == 'off' else ["         ALL         "]
            self.connectionlist_optionmenu.configure(values=connection_list_option)
            self.connectionlist_optionmenu.set(connection_list_option[0])
            self.tgt_drone_label.configure(text=f"Target Vehicle : \n{connection_list_option[0]}")
        else:
            connection_list_option = ['None']
            self.connectionlist_optionmenu.configure(values=connection_list_option)
            self.connectionlist_optionmenu.set(connection_list_option[0])

    def action_list_optionmenu_callback(self, choice):
        self.debug_print(f"action_list dropdown clicked: {choice}")

    def mode_list_optionmenu_callback(self, choice):
        self.debug_print(f"mode_list dropdown clicked: {choice}")


    def change_appearance_mode(self, option: str):
        self.debug_print(option)
        customtkinter.set_appearance_mode(option)
    # make static or move to different file
    def read_file(self, filename):
        self.debug_print(filename)
        try: # remove try bblock
            with open(filename, 'r') as inputfile:
                return [row[0] for row in csv.reader(inputfile, delimiter=',') if row]
        except FileNotFoundError:
            return ""

    def connect_swarm(self):
        self.swarm = Swarm(self.connection_strings, self.local_reference)
        self.connection_thread = Thread(target=self.swarm.connect, daemon=False)
        self.threads.append(self.connection_thread)
        self.connection_thread.start()
        self.connection_progressbar.configure(mode='indeterminate')
        self.connection_progressbar.start()

    def disconnect_swarm(self):
        self.monitor_position = False
        disconnection_thread = Thread(target=self.swarm.disconnect, daemon=False)
        # self.threads.append(self.disconnection_thread)
        disconnection_thread.start()
        self.debug_print("Disconnection Thread or process started.")
        self.swarm = None
        self.connection_strings = None
        self.connection_progressbar.set(0.)
        for path in self.drone_paths:
            path.delete() if self.drone_paths else self.debug_print(f"No prior paths")
        for marker in self.drone_markers:
            marker.delete() if self.drone_paths else self.debug_print(f"No prior markers")     

    def position_monitor(self):
        while self.connection_thread.is_alive():
            time.sleep(1.0)

        self.connection_progressbar.stop()
        self.connection_progressbar.set(1.)
        self.connection_progressbar.configure(mode='determinate')
        progressbar_dir = 1
        
        fleet_size = len(self.swarm.drones)
        while self.monitor_position:
            self.connection_progressbar.set(0.)

            if self.connection_strings and self.local_reference is not None and self.swarm.drones:
                for marker in self.drone_markers: marker.delete()
                for drone in self.swarm.drones:
                    if drone.connected:
                        lattitude, longitude, altitude = drone.get_position_lla()
                        state = "ARMED" if drone.armed else "DISARMED"
                        self.drone_markers.append(self.map_widget.set_marker(lattitude, longitude, text=f"Drone {drone.index}| {drone.mode} | {state} | {altitude:.1f}m"))

                        progressbar_dir *= -1
                        self.connection_progressbar.set((drone.index + 1) / fleet_size)
            # self.connection_progressbar.set(1.)

            time.sleep(1.0)
            
        try:
            for marker in self.drone_markers:
                marker.delete()
        finally:
            return

    def set_mode(self, mode):
        if self.switch.get() == "on":
            try:
                self.swarm.do_parallel(lambda drone: drone.set_mode(mode))
            except Exception as e:
                self.debug_print(f"{e}")
        else:
            target_drone_address = self.connectionlist_optionmenu.get()
            self.debug_print(f"setting mode {mode} for {target_drone_address}")
            for drone in self.swarm.drones:
                if drone.connection_string == target_drone_address:
                    try:
                        drone.set_mode(mode)
                    except Exception as e:
                        self.debug_print(f"{e}")
                else:
                    print(
                        f"Not changing mode for {drone.connection_string}")

    def set_state(self, state):
        if self.switch.get() == "on":
            if state == "ARM":
                try:
                    self.swarm.do_parallel(lambda drone: drone.arm())
                except Exception as e:
                    self.debug_print(f"{e}")
                    return

            if state == "DISARM":
                try:
                    self.swarm.do_parallel(lambda drone: drone.disarm())
                except Exception as e:
                    self.debug_print(f"{e}")
                    return
            self.debug_print("setting state  " + state + "ED  for all drones")

        else:
            target_drone_address = self.connectionlist_optionmenu.get()
            self.debug_print(f"setting state {state}ED for {target_drone_address}")

            for drone in self.swarm.drones:
                try:
                    if state == "ARM":
                        drone.arm() if drone.connection_string == target_drone_address else print(f"Not changing state for {drone.connection_string}")
                        return
                    if state == "DISARM":
                        drone.disarm() if drone.connection_string == target_drone_address else print(f"Not changing state for {drone.connection_string}")
                        return

                except Exception as e:
                    self.debug_print(f"{e}")
                    return

    def goto_marker(self):                
        for drone in self.swarm.drones:

            if not self.position_q.empty():
                drone.goto(self.position_q.get())


    @staticmethod
    def is_float(element: Any) -> bool:
        try:
            float(element)
            return True
        except ValueError:
            return False

    def takeoff(self, alt):
        # Don't if already in air
        self.debug_print(f"Target Takeoff Altitude : {alt} m")
        if self.switch.get() == "on":
            self.swarm.do_parallel(lambda drone: drone.set_mode("GUIDED"))
            self.swarm.do_parallel(lambda drone: drone.arm())
            self.swarm.do_parallel(lambda drone: drone.takeoff(alt))

        else:
            target_drone_address = self.connectionlist_optionmenu.get()
            self.debug_print(f"{target_drone_address}  Taking off")
            for drone in self.swarm.drones:
                if drone.connection_string == target_drone_address:
                    drone.set_mode("GUIDED")
                    drone.arm()
                    drone.takeoff(alt)
                else:
                    self.debug_print(f"{drone.connection_string} Not Taking off")

    def on_closing(self, event=0):

        self.monitor_position = False
        try:
            if self.swarm is not None:
                self.disconnect_swarm()

        finally:
            self.destroy()

        for thread in self.threads:
            print(f"{thread}")
            thread.join()

    def start(self):
        self.mainloop()


if __name__ == "__main__":
    print(sys.version)
    app = App()
    app.start()
    exit(0)
