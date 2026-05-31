# UI/

| File                  | Role                                                                  |
|-----------------------|-----------------------------------------------------------------------|
| `ui_top.py`           | `TopPanel` — composites HUD, menus, connection overlays onto frames   |
| `touch_interface.py`  | `TouchInterface` — evdev reader, maps touch coordinates to commands   |
| `touch_config.py`     | Device discovery, axis calibration                                    |
| `touch_settings.json` | Hit-box zone definitions. Edit without touching Python.               |
| `themes/chalk.py`     | Colour constants, font path, opacity values used across all renderers |

Touch coordinate origin: `(0,0)` = top-left of the 480×320 display.
