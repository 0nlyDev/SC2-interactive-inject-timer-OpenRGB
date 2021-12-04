import threading
import time
from datetime import datetime, timedelta

from pynput.keyboard import Key, Listener
from openrgb import OpenRGBClient
from openrgb.utils import RGBColor

client = OpenRGBClient()
print(client)
print(client.devices)
client.clear()

stop_timers = Key.f8
camera_hotkeys = [Key.f1, Key.f2, Key.f3, Key.f4, Key.f5, Key.f6]
inject_hotkey = 'w'
minimum_time_window = timedelta(seconds=.6)
min_timer_value = 0
cycle_length = timedelta(seconds=31)  # change 31 to the exact time the queens get 25 energy
throbbing_frequency = timedelta(seconds=0.1)
miss_click_tolerance = 2

last_two_keys_pressed = []
time_since_last_reset = 0


class Timer(object):
    def __init__(self):
        self.last_reset = datetime.now() + cycle_length
        self.first_reset = False
        self.rgb_time_off = datetime.now() + throbbing_frequency
        self.rgb_on_off = True

    def update_last_reset(self):
        self.last_reset = datetime.now() + cycle_length
        self.first_reset = True

    def update_rbg_lights_off(self):
        self.rgb_time_off = datetime.now() + throbbing_frequency
        self.rgb_on_off = not self.rgb_on_off


def main():
    thread2 = threading.Thread(target=update_rgb, args=())
    thread2.start()

    with Listener(on_press=get_key) as listener:
        listener.join()


def get_key(key):
    # print('Key pressed:', key)
    try:
        if key == stop_timers:
            timer.first_reset = False
            last_two_keys_pressed.clear()
            print('Deactivated - Inject a hatchery and the Macro Cycle Timers will start automatically')
        elif key in camera_hotkeys:
            last_two_keys_pressed.append([key, datetime.now()])
        elif key.char == inject_hotkey:
            last_two_keys_pressed.append([key.char, datetime.now()])
        else:
            last_two_keys_pressed.append([key, datetime.now()])
    except AttributeError:
        pass

    del last_two_keys_pressed[:-(miss_click_tolerance + 2)]  # truncate list
    reset_cycle()


def reset_cycle():
    now = datetime.now()
    camera_hotkey_log = [i for i in last_two_keys_pressed if i[0] in camera_hotkeys]
    inject_hotkey_log = [i for i in last_two_keys_pressed if i[0] == inject_hotkey]

    try:
        youngest_ind = max(ind for ind, dt in enumerate(camera_hotkey_log) if dt[1] <= now)
        camera_hotkey_log = camera_hotkey_log[youngest_ind]
    except ValueError:
        camera_hotkey_log = []

    try:
        youngest_ind = max(ind for ind, dt in enumerate(inject_hotkey_log) if dt[1] <= now)
        inject_hotkey_log = inject_hotkey_log[youngest_ind]
    except ValueError:
        inject_hotkey_log = []

    if camera_hotkey_log != [] and inject_hotkey_log != []:
        keys_pressed_time_difference = inject_hotkey_log[1] - camera_hotkey_log[1]
        if camera_hotkey_log[1] < inject_hotkey_log[1]:
            if keys_pressed_time_difference <= minimum_time_window:
                if now >= timer.last_reset or timer.first_reset is False:
                    inject_delay = (datetime.now() - timer.last_reset).total_seconds()
                    print('!!!QUEEN INJECT DETECTED - MACRO CYCLE COUNTDOWN STARTED!!! {} seconds'
                          .format(cycle_length.total_seconds()))
                    if timer.first_reset:
                        print('You are late on your Queen Injects by {} seconds'.format(inject_delay))
                    timer.update_last_reset()
                    last_two_keys_pressed.clear()
                else:
                    time_remaining_till_next_cycle_reset = (timer.last_reset - now).total_seconds()
                    print(time_remaining_till_next_cycle_reset, 'Seconds remaining before next macro cycle')
            elif now >= timer.last_reset:
                print('Too slow, minimum time from Camera keybind and Inject keybind is',
                      str(minimum_time_window.total_seconds()) + 'sec')
        # else:
        #     print('Incorrect order of key presses, to detect Inject cycle, frst press Camera keybind, followed by '
        #           'Inject keybind')


def normalize_and_clamp(val, min_val, max_val, min_clamp, max_clamp):
    normalized = (val - min_val) / (max_val - min_timer_value)
    normalized = int(float(255) * normalized)
    if normalized < min_clamp:
        normalized = min_clamp
    elif normalized > max_clamp:
        normalized = max_clamp
    return normalized


def throbbing_rgb(on_off):
    if on_off:
        return 255
    return 0


def update_rgb():
    # run continuous
    while True:
        time.sleep(0.1)
        time_remaining_till_next_cycle_reset = (timer.last_reset - datetime.now()).total_seconds()
        # print('time_remaining_till_next_cycle_reset', time_remaining_till_next_cycle_reset)
        if time_remaining_till_next_cycle_reset <= 0 or timer.first_reset is False:
            if (datetime.now() - timer.rgb_time_off) > throbbing_frequency:
                timer.update_rbg_lights_off()
            red_val = 255
            blue_val = 0
            if timer.first_reset:
                red_val = throbbing_rgb(timer.rgb_on_off)
                print('!!!INJECT!!!')

            if red_val == 255:
                green_val = 0
            else:
                green_val = 255
            if not timer.first_reset:
                red_val = green_val = 0
                blue_val = 255
            client.set_color(RGBColor(red_val, green_val, blue_val))
        else:
            time_passed_from_last_cycle_reset = cycle_length.total_seconds() - time_remaining_till_next_cycle_reset
            red_val = normalize_and_clamp(time_passed_from_last_cycle_reset, min_timer_value,
                                          cycle_length.total_seconds(), 0, 255)
            green_val = normalize_and_clamp(time_remaining_till_next_cycle_reset, min_timer_value,
                                            cycle_length.total_seconds(), 0,
                                            255)
            client.set_color(RGBColor(red_val, green_val, 0))


if __name__ == "__main__":
    timer = Timer()
    main()
