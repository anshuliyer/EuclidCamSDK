# IO/

GPIO / evdev input stubs for running the firmware on a dev machine without real hardware.

On the Pi, the touchscreen is read directly by `UI/touch_interface.py` via evdev.  
On a dev machine, `keyboard_gpio_stubs.py` maps keyboard keys to the same commands.
