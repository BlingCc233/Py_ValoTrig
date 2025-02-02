#6408503233360301491522
#4695572066159822484296
#8990689134437374726797
#2541848224673017251568
#1148599472838751497909
#9155157050138017650674
#3933714307792373539061
#7155435608031828627699
import cv2 as c2
import time as t
import keyboard
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

#3612284081249116462070
import win32gui
import win32process
import win32con
import pythoncom



# UUID = "930d21cb1f964e8aad4bea898f06705b"
# Number lines can be added here
# UUID = "930d21cb1f964e8aad4bea898f06705b"

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
            elif key == b'\x02': # D key PR
                keybd_event(0x44, 0, 0, 0)
                keybd_event(0x44, 0, 2, 0)
            elif key == b'\x03': # A key PR
                keybd_event(0x41, 0, 0, 0)
                keybd_event(0x41, 0, 2, 0)
        except EOFError:
            break


# Helper function to send key press
def snd_key_evt(pipe):
    pipe.send(b'\x01')

def snd_counter_strafe_d(pipe):
    pipe.send(b'\x02')

def snd_counter_strafe_a(pipe):
    pipe.send(b'\x03')

# UUID = "930d21cb1f964e8aad4bea898f06705b"


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
        self.compensating = False

    #6010484127259241540730
    def capture_frame(self):
        while True:
            self.frame = self.camera.grab()
            t.sleep(self.frame_duration)  # Sleep to control FPS

    #1872519879357494096069
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
        
    #6702203205053086890734
    def counter_strafe(self, key):
        if key == 'a':
            self.compensating = True
            snd_counter_strafe_d(self.pipe)
            t.sleep(0.005)
            self.compensating = False
        elif key == 'd':
            self.compensating = True
            snd_counter_strafe_a(self.pipe)
            t.sleep(0.005)
            self.compensating = False

    #8220933897305363393019
    def setup_auto_counter_strafe(self):
        try:
            if not self.compensating:
                keyboard.on_release_key('a', lambda e: th.Thread(target=self.counter_strafe, args=('a',)).start())
                keyboard.on_release_key('d', lambda e: th.Thread(target=self.counter_strafe, args=('d',)).start())
        except:
            pass

    #8078591336375097861984
    def trigger(self):
        global HoldMode

        while True:
            if self.compensating:
                continue

            w_pressed = wapi.GetAsyncKeyState(0x57) < 0
            a_pressed = wapi.GetAsyncKeyState(0x41) < 0
            s_pressed = wapi.GetAsyncKeyState(0x53) < 0
            d_pressed = wapi.GetAsyncKeyState(0x44) < 0
            
            if w_pressed or a_pressed or s_pressed or d_pressed:
                self.keys_pressed = True
                continue
            elif self.keys_pressed:
                t.sleep(0.1)
                self.keys_pressed = False



            #1957318339966642693412
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

        #8361212090270307773148
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
        th.Thread(target=trgbt.setup_auto_counter_strafe).start()
        th.Thread(target=toggle_hold_mode).start()
        p_proc.join()
    
    finally:
        pythoncom.CoUninitialize()


#7175343535290797461521
#2450751025628005268352
#1557510631359455073167
#9742024989047569085814
#3831446036707954084364
#3584478742755646275023
#5620448443600959192645
#4268451040267018835222
#8702515407104958518393
