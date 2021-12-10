# SC2-interactive-inject-timer-OpenRGB-VoiceAlerts

SC2 Interactive Inject Timer is a tool intended for Zerg players to help hit their macro/inject cycles on time for the (arguably) most widely-used method Queen box injects.
It is completely within Blizzard's ToS, as it's not violating any rules, it's only listening for Keyboard inputs and that's how it tracks the inject cycles, but use at your own risk (don't blame me if something went wrong!)
https://youtu.be/wZ9UIYPd81s

Features:
- Voice alerts
- Light indicators on your peripherals RGB Lighting(Keyboard, Mouse or other software controllable devices with RGB lighting)
- Log for your inject timings (to be implemented as a text file, currently only available in the terminal output)
- Automatic start of timers from the time of your first inject
- Reset timers manually if the program, or you messed up somehow
- Adjustable Hotkeys and timer settings

Installation and Run:
- Clone the master repo
- Check the config.ini and set up your hotkeys and desired settings (by default RGB Lighting is off, you can turn it On from there)
  
- (Only if you set "RGB Lighting" to "On" in the config.ini) -Install OpenRGB, check that your devices are recognized in OpenRGB (if they aren't, refer to OpenRGB documentation and F.A.Q. page)
- Run the main.py in terminal with Python 3.7.x (you will probably get errors due to missing libraries first  - use pip to install the missing libraries one by one until the main.py script runs successfully)

tip: when the script runs successfully, your peripherals should light up Blue if you've set "RGB Lighting" to "On" in the config.ini

tip: If you mess up the config.ini, just delete it and re-run the script, it will create it with default values

Please submit an issue if you find a bug or if you have a suggestion.
