#3459025648430994624201
#1186721021058413180495
#2243882878225775872928
#7761950836317897126602
#1620609396124117379016
#1613542207172278174179
#5440023840278810688259
#6151329269214048521032
import cv2 as c2
import time as t
import numpy as np
import ctypes as c
import win32api as wapi
import threading as th
import bettercam as bcam
from multiprocessing import Pipe as p, Process as proc
from ctypes import windll as wdl
import os as os
import json as js
import uuid

#2641754703186231583335
import win32gui
import win32process
import win32con
import pythoncom



# UUID = "53d5bb264e084757bdfe36c436656133"
# Number lines can be added here
# UUID = "53d5bb264e084757bdfe36c436656133"

HoldMode = True

def set_window_title():
    random_uuid = str(uuid.uuid4())
    current_pid = os.getpid()
    hwnd = win32gui.GetForegroundWindow()
    win32gui.SetWindowText(hwnd, random_uuid)
    handle = win32process.GetCurrentProcess()
    win32process.SetProcessWorkingSetSize(handle, -1, -1)

def toggle_hold_mode():
    global HoldMode
    while True:
        if wapi.GetAsyncKeyState(0x72) < 0:
            HoldMode = not HoldMode
            print("HoldMode" ,HoldMode)
            if HoldMode:
                print("\a")
            t.sleep(0.2)
        t.sleep(0.001)

# Utility to clear the terminal
def cl():
    os.system('cls' if os.name == 'nt' else 'clear')
    console = win32gui.GetForegroundWindow()
    win32gui.ShowWindow(console, win32con.SW_HIDE)


# Function to simulate keyboard events
def kbd_evt(pipe):
    keybd_event = wdl.user32.keybd_event
    while True:
        try:
            key = pipe.recv()
            if key == b'\x01':
                keybd_event(0x4F, 0, 0, 0)  # O key press
                t.sleep(0.18 + np.random.uniform(0, 0.02))  # Sleep for 180~200ms
                keybd_event(0x4F, 0, 2, 0)  # O key release
        except EOFError:
            break


# Helper function to send key press
def snd_key_evt(pipe):
    pipe.send(b'\x01')

# UUID = "53d5bb264e084757bdfe36c436656133"


# Triggerbot class that contains the main logic
class Trgbt:
    def __init__(self, pipe, keybind, fov, hsv_range, shooting_rate, fps):
        user32 = wdl.user32
        self.WIDTH, self.HEIGHT = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
        self.size = fov
        self.Fov = (
            int(self.WIDTH / 2 - self.size),
            int(self.HEIGHT / 2 - self.size),
            int(self.WIDTH / 2 + self.size),
            int(self.HEIGHT / 2 + self.size),
        )
        self.camera = bcam.create(output_idx=0, region=self.Fov)
        self.frame = None
        self.keybind = keybind
        self.pipe = pipe
        self.cmin, self.cmax = hsv_range
        self.shooting_rate = shooting_rate
        self.frame_duration = 1 / fps  # FPS to frame duration in seconds
        self.keys_pressed = False

    #7941508063743479767234
    def capture_frame(self):
        while True:
            self.frame = self.camera.grab()
            t.sleep(self.frame_duration)  # Sleep to control FPS

    #9843805889715163282552
    def detect_color(self):
        if self.frame is not None:
            hsv = c2.cvtColor(self.frame, c2.COLOR_RGB2HSV)

            # Convert HSV range to NumPy arrays if they're not already
            self.cmin = np.array(self.cmin, dtype=np.uint8)
            self.cmax = np.array(self.cmax, dtype=np.uint8)

            mask = c2.inRange(hsv, self.cmin, self.cmax)

            # Ignore the center 6x6 area
            center_x, center_y = mask.shape[1] // 2, mask.shape[0] // 2
            mask[center_y - 3:center_y + 3, center_x - 3:center_x + 3] = 0

            return np.any(mask)

    #4935475231381186642305
    def trigger(self):
        global HoldMode
        while True:
            if wapi.GetAsyncKeyState(0x57) < 0 or wapi.GetAsyncKeyState(0x41) < 0 or wapi.GetAsyncKeyState(
                    0x53) < 0 or wapi.GetAsyncKeyState(0x44) < 0:
                self.keys_pressed = True
                continue
            elif self.keys_pressed:
                t.sleep(0.1)  # Sleep for key_up_rec_time
                self.keys_pressed = False

            #1983460290257915328811
            if (HoldMode or wapi.GetAsyncKeyState(self.keybind) < 0):
                if (self.detect_color()):
                    snd_key_evt(self.pipe)
                    t.sleep(self.shooting_rate / 1000)  # Convert ms to seconds
            t.sleep(0.001)




# Function to load the configuration from a file
def load_cfg():
    with open('config.json', 'r') as cfg_file:
        return js.load(cfg_file)


if __name__ == "__main__":
    pythoncom.CoInitialize()
    try:
        set_window_title()
        cl()

        #9944402302385592231000
        parent_conn, child_conn = p()
        p_proc = proc(target=kbd_evt, args=(child_conn,))
        p_proc.start()

        # Load or create the configuration
        cfg = {}
        if os.path.exists('config.json'):
            cfg = load_cfg()
            print("Config loaded:")
            print(js.dumps(cfg, indent=4))
        else:
            exit(0)

        # Initialize and start the Triggerbot
        trgbt = Trgbt(parent_conn, cfg['keybind'], cfg['fov'], cfg['hsv_range'], cfg['shooting_rate'], cfg['fps'])
        th.Thread(target=trgbt.capture_frame).start()
        th.Thread(target=trgbt.trigger).start()
        th.Thread(target=toggle_hold_mode).start()
        p_proc.join()
    
    finally:
        pythoncom.CoUninitialize()


#9275074300072847716828
#9897976037895061869955
#4594930882483642291756
#3455790853996695602347
#9052186860220231049149
#5216664877689725846355
#3582686950830669612288
#6236070038334517647040
#2415098794989404391404
