#3734069754346917850084
#6293282125533079774221
#7643466630466666613679
#2060451345658758418172
#7549490605116744287243
#1298311208004673755785
#2961851017602988667084
#9039204316589850917553
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

#3877087012015648610201
import win32gui
import win32process
import win32con
import pythoncom



# UUID = "7d01fa78489748878f8f6007e1b8be94"
# Number lines can be added here
# UUID = "7d01fa78489748878f8f6007e1b8be94"

HoldMode = True

def set_window_title():
    random_uuid = str(uuid.uuid4())
    current_pid = os.getpid()
    hwnd = win32gui.GetForegroundWindow()
    win32gui.SetWindowText(hwnd, random_uuid)
    handle = win32process.GetCurrentProcess()
    # win32process.SetProcessWorkingSetSize(handle, -1, -1)

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

# UUID = "7d01fa78489748878f8f6007e1b8be94"


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

    #3910050916827700114520
    def capture_frame(self):
        while True:
            self.frame = self.camera.grab()
            t.sleep(self.frame_duration)  # Sleep to control FPS

    #1835590642045109253185
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
        
    #8614041754246446194588
    def counter_strafe(self, key):
        if key == 'a' and not wapi.GetAsyncKeyState(0x44) < 0:  # Only if D is not pressed
            self.compensating = True
            snd_counter_strafe_d(self.pipe)
            t.sleep(0.005)
            self.compensating = False
        elif key == 'd' and not wapi.GetAsyncKeyState(0x41) < 0:  # Only if A is not pressed
            self.compensating = True
            snd_counter_strafe_a(self.pipe)
            t.sleep(0.005)
            self.compensating = False

    #4846697355452822741121
    def setup_auto_counter_strafe(self):
        try:
            if not self.compensating:
                self.last_key_released = None
                
                def handle_a_release(e):
                    if not wapi.GetAsyncKeyState(0x44) < 0:  # If D is not pressed
                        th.Thread(target=self.counter_strafe, args=('a',)).start()
                    
                def handle_d_release(e):
                    if not wapi.GetAsyncKeyState(0x41) < 0:  # If A is not pressed
                        th.Thread(target=self.counter_strafe, args=('d',)).start()
                    
                keyboard.on_release_key('a', handle_a_release)
                keyboard.on_release_key('d', handle_d_release)
        except:
            pass

    #8321307368130417739692
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



            #5392254571585205541601
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

        #8548166689599374014310
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
        #th.Thread(target=trgbt.setup_auto_counter_strafe).start()
        th.Thread(target=toggle_hold_mode).start()
        p_proc.join()
    
    finally:
        pythoncom.CoUninitialize()


#4440184344695227868240
#8206999647518547357339
#8578541328482484082844
#7755050988132424355684
#4385600764196089638199
#5805907557001422591918
#3132703058425513774641
#7530259195987404875556
#2072731673872906122265
