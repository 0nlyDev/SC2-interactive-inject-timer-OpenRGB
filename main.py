import threading
import time
from datetime import datetime, timedelta

import configparser
from pynput.keyboard import Key, Listener
from openrgb import OpenRGBClient
from openrgb.utils import RGBColor
from playsound import playsound

client = OpenRGBClient()
print(client)
print(client.devices)
client.clear()
[d.set_mode('direct') for d in client.devices]

camera_hotkeys = [Key.f1, Key.f2, Key.f3, Key.f4, Key.f5, Key.f6]
stop_timers_hotkey = Key.f12
reset_timers_hotkey = Key.f8
inject_hotkey = 'w'
voice_alerts = True
minimum_time_window = timedelta(seconds=1.1)
min_timer_value = 0
cycle_length = timedelta(seconds=30)
throbbing_frequency = timedelta(seconds=0.1)
miss_click_tolerance = 1

last_two_keys_pressed = []
time_since_last_reset = 0


class Timer(object):
    def __init__(self):
        self.last_reset = datetime.now() + cycle_length
        self.first_reset = False
        self.rgb_time_off = datetime.now() + throbbing_frequency
        self.rgb_on_off = True
        self.sound_thread = threading.Thread(target=play_sound, kwargs={'sound': ''})

    def create_sound_thread(self, sound):
        self.sound_thread = threading.Thread(target=play_sound, kwargs={'sound': sound})

    def update_last_reset(self):
        self.last_reset = datetime.now() + cycle_length
        self.first_reset = True

    def update_rbg_lights_off(self):
        self.rgb_time_off = datetime.now() + throbbing_frequency
        self.rgb_on_off = not self.rgb_on_off


def removeInlineComments(cfgparser, delimiter):
    for section in cfgparser.sections():
        [cfgparser.set(section, item[0], item[1].split(delimiter)[0].strip()) for item in cfgparser.items(section)]


def create_default_config():
    config = configparser.ConfigParser(allow_no_value=True)
    config.optionxform = str
    config['HOTKEYS'] = {';Make sure that the hotkeys listed bellow are not used in-game:': None,
                         'Queen Inject': 'W',
                         'Jump to Location 1': 'F1',
                         'Jump to Location 2': 'F2',
                         'Jump to Location 3': 'F3',
                         'Jump to Location 4': 'F4',
                         'Jump to Location 5': 'F5',
                         'Jump to Location 6': 'F6',
                         'Jump to Location 7': 'F7',
                         'Jump to Location 8': 'F8',
                         'Reset Timers': 'F9 ;Resets the Inject Cycle timer (you can use this in-game to quickly '
                                         'reset the timers if you messed up somehow or at the star of the game when '
                                         'you possibly don\'t use the camera hotkey yet)',
                         'Stop Timers': 'F12 ;Resets and stops the Inject Cycle timer. To start again, just do '
                                        'another Inject Cycle'}
    config['ALERTS'] = {';Chose what type of alerts you want to use #': None,
                        'RGB Lighting': 'On ;On/Off',
                        '\tThrobbing Frequency': '0.1 ;Seconds',
                        'Voice alerts': 'On ;On/Off'}
    config['ADVANCED'] = {';Settings that changes the behaviour of how and when an Inject Cycle is registered:': None,
                          'Inject Cooldown': '30 ;Seconds',
                          'Miss-click Tolerance': '1 ;This value determines how many other keys you can press after '
                                                  'you pressed the camera hotkey and the inject the hotkey and still '
                                                  'register the sequence as valid inject cycle',
                          'Maximum Time Window': '1.1 ;Seconds - This value specifies the maximum time between key '
                                                 'presses that the program will register as valid inject cycle. If '
                                                 'you find that your injects are not being registered, you can try to '
                                                 'increase this value'
                          }

    with open('config.ini', 'w') as configfile:
        config.write(configfile)


def read_config_ini():
    config = configparser.ConfigParser()
    config.read('config.ini')
    removeInlineComments(config, ';')
    print(config.sections())
    print(config['ALERTS']['RGB Lighting'])


def main():
    thread2 = threading.Thread(target=update_rgb, args=())
    thread2.start()

    with Listener(on_press=get_key) as listener:
        listener.join()


def get_key(key):
    # print('Key pressed:', key)
    try:
        if key == stop_timers_hotkey:
            timer.first_reset = False
            last_two_keys_pressed.clear()
            timer.create_sound_thread(r'sounds\\deactivated.wav')
            timer.sound_thread.start()
            print('Deactivated - Inject a hatchery and the Macro Cycle Timers will start automatically')
        elif key == reset_timers_hotkey:
            timer.update_last_reset()
            last_two_keys_pressed.clear()
            print('Timers reset')
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


def play_sound(sound=None):
    if voice_alerts:
        playsound(sound)


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
                if not timer.sound_thread.is_alive():
                    timer.create_sound_thread(r'sounds\\inject.wav')
                    timer.sound_thread.start()
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
    create_default_config()
    read_config_ini()
    timer = Timer()
    main()
