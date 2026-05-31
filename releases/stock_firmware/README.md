# firmware/python

Entry point: `camera.py` → imports config → calls `main.run()`.

`main.py` contains the full class hierarchy:

- **`CameraEngine`** — framebuffer loop, composes all subsystems
- **`InputHandler`** — maps touch commands to config mutations
- **`GalleryManager`** — photo listing, navigation, deletion
- **`ServerManager`** — Flask subprocess lifecycle
- **`CameraMode`** base → `StandardMode`, `FilterMode`, `LowLightMode`

## Adding a filter

1. Add `filters/my_filter.py` with `apply_my_filter(pil_img) -> Image`.
2. `from filters import my_filter` in `main.py`.
3. Add `FilterMode("Name", my_filter)` to `CameraEngine.__init__` modes list.
4. Add the display string to `UI/ui_top.py` → `_draw_menu` items list.
