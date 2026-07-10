from PIL import Image
import sys

def convert_to_rgb565(input_path, output_path):
    img = Image.open(input_path).convert('RGB')
    # Resize to match ILI9341
    img = img.resize((320, 240))
    pixels = img.load()
    
    with open(output_path, 'wb') as f:
        for y in range(img.height):
            for x in range(img.width):
                r, g, b = pixels[x, y]
                # RGB565 encoding: R(5) G(6) B(5)
                rgb565 = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
                # ILI9341 expects Big-Endian over SPI
                f.write(bytes([rgb565 >> 8, rgb565 & 0xFF]))

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <input.png/jpg> <output.rgb565>")
        sys.exit(1)
    convert_to_rgb565(sys.argv[1], sys.argv[2])
    print(f"Successfully converted {sys.argv[1]} to {sys.argv[2]} (RGB565 Raw)")
