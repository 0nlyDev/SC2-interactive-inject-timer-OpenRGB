import threading
import time
import os
from datetime import datetime, timedelta

import configparser
from pynput.keyboard import Key, Listener
from pynput import keyboard
from playsound import playsound

last_two_keys_pressed = []
time_since_last_reset = 0


class Vals():
    def __init__(self):
        self.timer_length = timedelta(seconds=30)  # Time between injects
        self.min_timer_value = 0

        self.inject_hotkey = 'w'
        self.camera_hotkeys = []
        self.stop_timers_hotkey = Key.f12
        self.reset_timers_hotkey = Key.f9

        self.use_voice_alerts = True
        self.min_time_between_next_voice_alert = timedelta(seconds=5)
        self.time_since_last_voice_alert = datetime.now() - self.min_time_between_next_voice_alert

        self.use_rgb_lighting = True
        self.throbbing_frequency = timedelta(seconds=0.1)

        self.miss_click_tolerance = 1
        self.max_time_between_keyboard_inputs = timedelta(seconds=1.1)


class Timer(object):
    def __init__(self):
        self.last_reset = datetime.now() + vals.timer_length
        self.first_reset = False
        self.rgb_time_off = datetime.now() + vals.throbbing_frequency
        self.rgb_on_off = True
        self.sound_thread = threading.Thread(target=play_sound, kwargs={'sound': ''})

    def create_sound_thread(self, sound):
        self.sound_thread = threading.Thread(target=play_sound, kwargs={'sound': sound})

    def update_last_reset(self):
        self.last_reset = datetime.now() + vals.timer_length
        self.first_reset = True

    def update_rbg_lights_off(self):
        self.rgb_time_off = datetime.now() + vals.throbbing_frequency
        self.rgb_on_off = not self.rgb_on_off


def removeInlineComments(cfgparser, delimiter):
    for section in cfgparser.sections():
        [cfgparser.set(section, item[0], item[1].split(delimiter)[0].strip()) for item in cfgparser.items(section)]


def create_default_config():
    config = configparser.ConfigParser(allow_no_value=True)
    config.optionxform = str
    config['NOTES'] = {';The main.py script must be restarted for any changes to take effect made to this file': None}
    config['HOTKEYS'] = {';Make sure that the hotkeys listed bellow are not used in-game (!combination of hotkeys like '
                         '"shift+f1" currently are not accepted!):': None,
                         'Queen Inject': 'w',
                         'Jump to Location 1': 'f1',
                         'Jump to Location 2': 'f2',
                         'Jump to Location 3': 'f3',
                         'Jump to Location 4': 'f4',
                         'Jump to Location 5': 'f5',
                         'Jump to Location 6': 'f6',
                         'Jump to Location 7': 'f7',
                         'Jump to Location 8': 'f8',
                         'Reset Timers': 'f9 ;Resets the Inject Cycle timer (you can use this in-game to quickly '
                                         'reset the timers if you messed up somehow or at the star of the game when '
                                         'you possibly don\'t use the camera hotkey yet)',
                         'Stop Timers': 'f12 ;Resets and stops the Inject Cycle timer. To start again, just do '
                                        'another Inject Cycle'}
    config['ALERTS'] = {';Chose what type of alerts you want to use #': None,
                        'RGB Lighting': 'Off ;On/Off - By default it\'s set to "Off", if you want to use RGB '
                                        'Lighting, you will have to download and install OpenRGB first, then run it '
                                        'and make sure that your devices are detect in OpenRGB, then start the SDK '
                                        'Server from OpenRGB and only then run the script',
                        'Throbbing Frequency': '0.1 ;Seconds',
                        'Voice Alerts': 'On ;On/Off',
                        'Minimum Time Between Voice Alerts': '5 ;Seconds - If you want to have only 1 voice alert per '
                                                             'inject cycle, set this value to the same value as the '
                                                             '"Inject Cooldown" bellow. If you want annoying voice '
                                                             'alert without a delay, set this value to 0'}
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

    for k, v in config['HOTKEYS'].items():
        if len(v) > 1:
            hotkey = keyboard.HotKey.parse('<' + v.lower() + '>')[0]
        else:
            hotkey = keyboard.HotKey.parse(v.lower())[0]
        if k == 'queen inject':
            vals.inject_hotkey = hotkey
        elif k.startswith('jump'):
            vals.camera_hotkeys.append(hotkey)
        elif k == 'reset timers':
            vals.reset_timers_hotkey = hotkey
        elif k == 'stop timers':
            vals.stop_timers_hotkey = hotkey

    for k, v in config['ALERTS'].items():
        if k == 'rgb lighting':
            if v.lower() != 'on':
                vals.use_rgb_lighting = False
        elif k == 'throbbing frequency':
            if v.replace('.', '').isdigit():
                vals.throbbing_frequency = timedelta(seconds=float(v))
        elif k == 'voice alerts':
            if v.lower() != 'on':
                vals.use_voice_alerts = False
        elif k == 'minimum time between voice alerts':
            if v.replace('.', '').isdigit():
                vals.min_time_between_next_voice_alert = timedelta(seconds=float(v))

    for k, v in config['ADVANCED'].items():
        if k == 'inject cooldown':
            if v.replace('.', '').isdigit():
                vals.timer_length = timedelta(seconds=float(v))
        if k == 'maximum time window':
            if v.replace('.', '').isdigit():
                vals.max_time_between_keyboard_inputs = timedelta(seconds=float(v))
        if k == 'miss-click tolerance':
            if v.isdigit():
                vals.miss_click_tolerance = int(v)


def main():
    thread2 = threading.Thread(target=update_rgb, args=())
    thread2.start()

    with Listener(on_press=get_key) as listener:
        listener.join()


def get_key(key):
    # print('Key pressed:', key)
    try:
        if key == vals.stop_timers_hotkey:
            timer.first_reset = False
            last_two_keys_pressed.clear()
            timer.create_sound_thread(r'sounds\\deactivated.wav')
            timer.sound_thread.start()
            print('Deactivated - Inject a hatchery and the Macro Cycle Timers will start automatically')
        elif key == vals.reset_timers_hotkey:
            timer.update_last_reset()
            last_two_keys_pressed.clear()
            print('Timers reset')
        elif key in vals.camera_hotkeys:
            last_two_keys_pressed.append([key, datetime.now()])
        elif key.char == vals.inject_hotkey:
            last_two_keys_pressed.append([key.char, datetime.now()])
        else:
            last_two_keys_pressed.append([key, datetime.now()])
    except AttributeError:
        pass

    del last_two_keys_pressed[:-(vals.miss_click_tolerance + 2)]  # truncate list
    reset_cycle()


def reset_cycle():
    now = datetime.now()
    camera_hotkey_log = [i for i in last_two_keys_pressed if i[0] in vals.camera_hotkeys]
    inject_hotkey_log = [i for i in last_two_keys_pressed if i[0] == vals.inject_hotkey]

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
            if keys_pressed_time_difference <= vals.max_time_between_keyboard_inputs:
                if now >= timer.last_reset or timer.first_reset is False:
                    inject_delay = (datetime.now() - timer.last_reset).total_seconds()
                    print('!!!QUEEN INJECT DETECTED - MACRO CYCLE COUNTDOWN STARTED!!! {} seconds'
                          .format(vals.timer_length.total_seconds()))
                    if timer.first_reset:
                        print('You are late on your Queen Injects by {} seconds'.format(inject_delay))
                    timer.update_last_reset()
                    last_two_keys_pressed.clear()
                else:
                    time_remaining_till_next_cycle_reset = (timer.last_reset - now).total_seconds()
                    print(time_remaining_till_next_cycle_reset, 'Seconds remaining before next macro cycle')
            elif now >= timer.last_reset:
                print('Too slow, minimum time from Camera keybind and Inject keybind is',
                      str(vals.max_time_between_keyboard_inputs.total_seconds()) + 'sec')
        # else:
        #     print('Incorrect order of key presses, to detect Inject cycle, frst press Camera keybind, followed by '
        #           'Inject keybind')


def normalize_and_clamp(val, min_val, max_val, min_clamp, max_clamp):
    normalized = (val - min_val) / (max_val - vals.min_timer_value)
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
    if vals.use_voice_alerts:
        if 'inject.wav' in sound:
            time_until_next_voice_alert = (datetime.now() - vals.time_since_last_voice_alert).total_seconds()
            if time_until_next_voice_alert >= vals.min_time_between_next_voice_alert.total_seconds():
                vals.time_since_last_voice_alert = datetime.now()
                playsound(sound)
        else:
            playsound(sound)


def update_rgb():
    while True:
        time.sleep(0.1)
        time_remaining_till_next_cycle_reset = (timer.last_reset - datetime.now()).total_seconds()
        # print('time_remaining_till_next_cycle_reset', time_remaining_till_next_cycle_reset)
        if time_remaining_till_next_cycle_reset <= 0 or timer.first_reset is False:
            if (datetime.now() - timer.rgb_time_off) > vals.throbbing_frequency:
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
            if vals.use_rgb_lighting:
                client.set_color(RGBColor(red_val, green_val, blue_val))
        else:
            time_passed_from_last_cycle_reset = vals.timer_length.total_seconds() - time_remaining_till_next_cycle_reset
            red_val = normalize_and_clamp(time_passed_from_last_cycle_reset, vals.min_timer_value,
                                          vals.timer_length.total_seconds(), 0, 255)
            green_val = normalize_and_clamp(time_remaining_till_next_cycle_reset, vals.min_timer_value,
                                            vals.timer_length.total_seconds(), 0,
                                            255)
            if vals.use_rgb_lighting:
                client.set_color(RGBColor(red_val, green_val, 0))


if __name__ == "__main__":
    vals = Vals()
    if not os.path.isfile('config.ini'):
        create_default_config()
    read_config_ini()
    if vals.use_rgb_lighting:
        from openrgb import OpenRGBClient
        from openrgb.utils import RGBColor

        client = OpenRGBClient()
        print(client)
        print(client.devices)
        client.clear()
        [d.set_mode('direct') for d in client.devices]

    timer = Timer()
    main()
