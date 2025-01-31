#2686186576886905604698
#4738117133721163294302
#1324330963635456269773
#3397120260856189693435
#7618502194193879589108
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

import win32gui
import win32process
import win32con


# UUID = "47e7190783f44aa5806c1f9bf7d8ead1"
# Number lines can be added here
# UUID = "47e7190783f44aa5806c1f9bf7d8ead1"

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

    def capture_frame(self):
        while True:
            self.frame = self.camera.grab()
            t.sleep(self.frame_duration)  # Sleep to control FPS

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

    set_window_title()
    cl()

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

#1176949343169135057719
#6806720406002702760748
#4063918400340015092434
#1606719867997230306836
#6366368272422377873386
