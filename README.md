# SC2-interactive-inject-timer-OpenRGB

SC2 Interactive Inject Timer is a tool intended for Zerg players to help hit their macro/inject cycles on time for the (arguably) most widely-used method Queen boxing for injects.

Features:
- Light indicators on your peripherals RGB Lighting(Keyboard, Mouse or other software controllable devices with RGB lighting)
- Voice reminders (to be implemented)
- Detailed stats log for your injects (to be implemented as a file, currently only available in terminal output)
- Automatic start of timers from the time of your first inject

Keybindings (defaults):  # currently only changeable in the main.py file - to be reimplemented to take them from a read file or a command line argument
- Camera keybind: F1, F2, F3, F4, F5, F6, F7
- Inject keybind: W
- Stop/Reset Timers: F8

Installation and Run:
- Install OpenRGB, check that your devices are recognized in OpenRGB (if they aren't, refer to OpenRGB documentation and F.A.Q. page)
- Clone the master repo
- Run the main.py in terminal with Python 3.7.x (you will probably get errors due to missing libraries first)
- Use pip to install the missing libraries one by one until the main.py script runs successfully
tip: when the script runs successfully, your peripherals should light up Blue
