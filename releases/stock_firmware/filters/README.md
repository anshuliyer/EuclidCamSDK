# filters/

Each file exposes one function: `apply_<name>_filter(pil_img) -> Image`.  
`FilterMode` in `main.py` discovers it automatically by name convention.

| Module              | Name      | Look                                          |
|---------------------|-----------|-----------------------------------------------|
| `glam.py`           | Glam      | High-contrast B&W, soft gaussian glow         |
| `film35mm.py`       | 35mm      | Point-and-shoot flash, lifted blue shadows    |
| `indoor.py`         | Indoor    | Warm shadows, low contrast, indoor flash feel |
| `italian_summer.py` | Summer    | Vivid Mediterranean warmth                    |
| `uni.py`            | UnI       | Vintage warm tint, lifted shadows             |
| `nostalgia.py`      | Nostalgia | Faded, desaturated retro                      |
| `low_light.py`      | —         | Used by `LowLightMode`, not in filter menu    |
