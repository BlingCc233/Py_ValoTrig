#1118941673698503659027
#3836304503371982644798
#7944314501019356637853
#3024349635178670667030
#5693455747788144345412
#3817998786913023228648
#3259578042865109032214
#3812008031881500983744
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

#7894953011454943139605
import win32gui
import win32process
import win32con
import pythoncom

import bezier
import math
import pydirectinput



# UUID = "3c1c2c8a4b644098b23800cb8430a511"
# Number lines can be added here
# UUID = "3c1c2c8a4b644098b23800cb8430a511"

HoldMode = True
global_target_pos = None
is_moving = False
u32 = wdl.user32
sWIDTH, sHEIGHT = u32.GetSystemMetrics(0), u32.GetSystemMetrics(1)
screen_center = (sWIDTH // 2, sHEIGHT // 2)
trig = None

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
    #win32gui.ShowWindow(console, win32con.SW_HIDE)


# Function to simulate keyboard events
def kbd_evt(pipe):
    keybd_event = wdl.user32.keybd_event
    while True:
        try:
            key = pipe.recv()
            if key == b'\x01':
                keybd_event(0x4F, 0, 0, 0)  # O key press
                t.sleep(0.18 + np.random.uniform(0, 0.02))  # Sleep for 180~200ms
                keybd_event(0X4F, 0, 2, 0)  # O key release
            elif key == b'\x02': # D key PR
                keybd_event(0x44, 0, 0, 0)
                keybd_event(0x44, 0, 2, 0)
            elif key == b'\x03': # A key PR
                keybd_event(0x41, 0, 0, 0)
                keybd_event(0x41, 0, 2, 0)
            else:
                move_mouse(key[0], key[1])
        except EOFError:
            break

class MouseInput(c.Structure):
    _fields_ = [("dx", c.c_long), ("dy", c.c_long), ("mouseData", c.c_ulong),
                ("dwFlags", c.c_ulong), ("time", c.c_ulong), ("dwExtraInfo", c.POINTER(c.c_ulong))]

class Input(c.Structure):
    _fields_ = [("type", c.c_ulong), ("mi", MouseInput)]

def move_mouse(x, y):
    input_data = Input()
    input_data.type = 0  # 0 means INPUT_MOUSE
    input_data.mi = MouseInput(x, y, 0, 0x0001, 0, None)
    c.windll.user32.SendInput(1, c.pointer(input_data), c.sizeof(input_data))

def move_mouse_bezier():
    global  is_moving, screen_center, trig
    while True:
        try:
            if trig == b'\x04':
                if global_target_pos is None:
                    continue


                dx = global_target_pos[0] - screen_center[0]
                dy = global_target_pos[1] + 5 - screen_center[1]


                length = math.sqrt(dx * dx + dy * dy)
                if length == 0:
                    continue

                perpendicular_x = -dy / length * 200
                perpendicular_y = dx / length * 200

                control_x = int(screen_center[0] + dx / 3 + perpendicular_x)
                control_y = int(screen_center[1] + dy / 3 + perpendicular_y)


                curve = bezier.Curve(np.array([
                    [screen_center[0], control_x, global_target_pos[0]],
                    [screen_center[1], control_y, global_target_pos[1]]
                ]), degree=2)

                edpi = 1600 * 0.26
                edpi = 1

                steps = 50
                last_x, last_y = screen_center
                total_movement = [0, 0]

                move_x, move_y = 0, 0

                for i in range(1, steps + 1):
                    point = curve.evaluate(i / steps)
                    current_x, current_y = point[0][0], point[1][0]

                    move_x = int((current_x - last_x) / edpi)
                    move_y = int((current_y - last_y) / edpi)


                    if move_x != 0 or move_y != 0:
                        total_movement[0] += move_x
                        total_movement[1] += move_y

                        wapi.mouse_event(0x0001, move_x, move_y, 0, 0)
                    last_x, last_y = current_x, current_y
                    t.sleep(0.001)

                trig = None
                is_moving = False

        except EOFError:
            break
        except Exception as e:
            print(f"Error in mouse movement: {str(e)}")
            is_moving = False




# Helper function to send key press
def snd_key_evt(pipe):
    pipe.send(b'\x01')

def snd_counter_strafe_d(pipe):
    pipe.send(b'\x02')

def snd_counter_strafe_a(pipe):
    pipe.send(b'\x03')

def snd_mouse_bezier(pipe):
    dx = global_target_pos[0] - screen_center[0]
    dy = global_target_pos[1] + 5 - screen_center[1]
    pipe.send([dx, dy])

# UUID = "3c1c2c8a4b644098b23800cb8430a511"





# Triggerbot class that contains the main logic
class Trgbt:
    def __init__(self, pipe, keybind, fov, hsv_range, shooting_rate, fps, aimkey):
        user32 = wdl.user32
        self.WIDTH, self.HEIGHT = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
        self.size = fov

        self.frame = None
        self.keybind = keybind
        self.aimkey = aimkey
        self.pipe = pipe
        self.cmin, self.cmax = hsv_range
        self.shooting_rate = shooting_rate
        self.frame_duration = 1 / fps  # FPS to frame duration in seconds
        self.keys_pressed = False
        self.compensating = False


        self.Fov = (
            int(self.WIDTH/2 - self.size),
            int(self.HEIGHT/2 - self.size),
            int(self.WIDTH/2 + self.size),
            int(self.HEIGHT/2 + self.size),
        )

        self.camera = bcam.create(output_idx=0, region=self.Fov)
        self.center_frame = None

    #4382952554731161751649
    def capture_frame(self):
        while True:
            self.frame = self.camera.grab()
            t.sleep(self.frame_duration)  # Sleep to control FPS

    def capture_center_frame(self):
        while True:
            self.center_frame = self.center_camera.grab()
            t.sleep(self.frame_duration)

    #9514773158647517381512
    def detect_color(self):
        if self.frame is not None:
            fov_frame = self.frame[
                        self.Fov[1]:self.Fov[3],
                        self.Fov[0]:self.Fov[2]
                        ]

            hsv = c2.cvtColor(fov_frame, c2.COLOR_RGB2HSV)
            self.cmin = np.array(self.cmin, dtype=np.uint8)
            self.cmax = np.array(self.cmax, dtype=np.uint8)
            mask = c2.inRange(hsv, self.cmin, self.cmax)

            #center_x, center_y = mask.shape[1] // 2, mask.shape[0] // 2
            #mask[center_y - 3:center_y + 3, center_x - 3:center_x + 3] = 0

            return np.any(mask)

    '''
    def detect_nearest_color(self):
        global global_target_pos, is_moving
        if is_moving or self.frame is None:
            return

        hsv = c2.cvtColor(self.frame, c2.COLOR_RGB2HSV)
        mask = c2.inRange(hsv, self.cmin, self.cmax)

        y_coords, x_coords = np.where(mask)
        if len(x_coords) == 0:
            global_target_pos = None
            return

        left, top, _, _ = self.center_region
        global_x = x_coords + left
        global_y = y_coords + top

        center_x, center_y = self.WIDTH // 2, self.HEIGHT // 2
        distances = (global_x - center_x) ** 2 + (global_y - center_y) ** 2
        min_idx = np.argmin(distances)

        global_target_pos = (int(global_x[min_idx]), int(global_y[min_idx]))
    '''

    def detect_nearest_color(self):
        global global_target_pos, is_moving
        if is_moving or self.frame is None:
            return

        hsv = c2.cvtColor(self.frame, c2.COLOR_RGB2HSV)
        mask = c2.inRange(hsv, self.cmin, self.cmax)

        y_coords, x_coords = np.where(mask)
        if len(x_coords) == 0:
            global_target_pos = None
            return

        left, top, _, _ = self.center_region
        global_x = x_coords + left
        global_y = y_coords + top

        min_y_idx = np.argmin(global_y)

        global_target_pos = (int(global_x[min_y_idx]), int(global_y[min_y_idx]))

    #7373701146630184445019
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

    #4435319091153687470313
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

    #3223662818711250799271
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



            #7009569812755599850258
            if (HoldMode or wapi.GetAsyncKeyState(self.keybind) < 0):
                if (self.detect_color()):
                    snd_key_evt(self.pipe)
                    t.sleep(self.shooting_rate / 1000)  # Convert ms to seconds
            t.sleep(0.001)

    #6083850430519779981294
    def aim(self):
        global trig
        while True:
            try:
                if wapi.GetAsyncKeyState(self.keybind) < 0:
                    self.detect_nearest_color()
                    if global_target_pos is not None:
                        print(global_target_pos)
                        # trig = b'\x04'
                        snd_mouse_bezier(self.pipe)
                    t.sleep(0.01)
                t.sleep(0.001)
            except Exception as e:
                print(f"Error in aim: {str(e)}")



# Function to load the configuration from a file
def load_cfg():
    with open('config.json', 'r') as cfg_file:
        return js.load(cfg_file)


if __name__ == "__main__":
    pythoncom.CoInitialize()
    try:
        set_window_title()
        cl()

        #3140992048788335099574
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
        trgbt = Trgbt(parent_conn, cfg['keybind'], cfg['fov'], cfg['hsv_range'], cfg['shooting_rate'], cfg['fps'], cfg['aimkey'])
        th.Thread(target=trgbt.capture_frame).start()
        th.Thread(target=trgbt.trigger).start()
        th.Thread(target=trgbt.setup_auto_counter_strafe).start()
        th.Thread(target=trgbt.aim).start()
        th.Thread(target=toggle_hold_mode).start()
        th.Thread(target=move_mouse_bezier).start()
        p_proc.join()

    finally:
        pythoncom.CoUninitialize()


#1232625813968751615749
#9129060232723033729252
#3041588664090137391337
#4335214122006219849337
#8301801576884138950403
#1974614468747997004310
#7366374775961901640648
#8551615038983233342233
#3882167944090683085795
