#include <stdint.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <linux/types.h>
#include <linux/spi/spidev.h>

#define SPI_DEVICE "/dev/spidev0.0"
#define PIN_DC 24
#define PIN_RST 25
#define WIDTH 320
#define HEIGHT 240

int spi_fd;
int fd_dc = -1;
int fd_rst = -1;

void gpio_export(int pin) {
    int fd = open("/sys/class/gpio/export", O_WRONLY);
    if (fd == -1) return;
    char buf[8];
    snprintf(buf, sizeof(buf), "%d", pin);
    write(fd, buf, strlen(buf));
    close(fd);
    usleep(10000); // Wait for udev
}

void gpio_dir_out(int pin) {
    char path[64];
    snprintf(path, sizeof(path), "/sys/class/gpio/gpio%d/direction", pin);
    int fd = open(path, O_WRONLY);
    if (fd == -1) return;
    write(fd, "out", 3);
    close(fd);
}

void gpio_open_fast() {
    char path[64];
    snprintf(path, sizeof(path), "/sys/class/gpio/gpio%d/value", PIN_DC);
    fd_dc = open(path, O_WRONLY);
    snprintf(path, sizeof(path), "/sys/class/gpio/gpio%d/value", PIN_RST);
    fd_rst = open(path, O_WRONLY);
}

void gpio_fast_dc(int val) {
    if (fd_dc != -1) write(fd_dc, val ? "1" : "0", 1);
}

void gpio_fast_rst(int val) {
    if (fd_rst != -1) write(fd_rst, val ? "1" : "0", 1);
}

void spi_transfer(uint8_t *data, int len) {
    struct spi_ioc_transfer tr = {
        .tx_buf = (unsigned long)data,
        .rx_buf = 0,
        .len = len,
        .speed_hz = 10000000,
        .delay_usecs = 0,
        .bits_per_word = 8,
    };
    ioctl(spi_fd, SPI_IOC_MESSAGE(1), &tr);
}

void write_command(uint8_t cmd) {
    gpio_fast_dc(0);
    spi_transfer(&cmd, 1);
}

void write_data(uint8_t data) {
    gpio_fast_dc(1);
    spi_transfer(&data, 1);
}

void write_data_buf(uint8_t *data, int len) {
    gpio_fast_dc(1);
    spi_transfer(data, len);
}

int main(int argc, char **argv) {
    if (argc < 2) {
        printf("Usage: %s <image.rgb565>\n", argv[0]);
        return 1;
    }

    // 1. Setup GPIOs
    gpio_export(PIN_DC);
    gpio_export(PIN_RST);
    gpio_dir_out(PIN_DC);
    gpio_dir_out(PIN_RST);
    gpio_open_fast();

    // 2. Hardware Reset
    gpio_fast_rst(1); usleep(5000);
    gpio_fast_rst(0); usleep(20000);
    gpio_fast_rst(1); usleep(150000);

    // 3. Open SPI
    spi_fd = open(SPI_DEVICE, O_RDWR);
    if (spi_fd < 0) { perror("SPI open"); return 1; }
    uint8_t mode = SPI_MODE_0;
    ioctl(spi_fd, SPI_IOC_WR_MODE, &mode);

    // 4. ILI9341 Initialization Sequence
    write_command(0x01); // Software reset
    usleep(50000);
    
    // Standard ILI9341 Power & VCOM Sequence
    write_command(0xEF); write_data(0x03); write_data(0x80); write_data(0x02);
    write_command(0xCF); write_data(0x00); write_data(0xC1); write_data(0x30);
    write_command(0xED); write_data(0x64); write_data(0x03); write_data(0x12); write_data(0x81);
    write_command(0xE8); write_data(0x85); write_data(0x00); write_data(0x78);
    write_command(0xCB); write_data(0x39); write_data(0x2C); write_data(0x00); write_data(0x34); write_data(0x02);
    write_command(0xF7); write_data(0x20);
    write_command(0xEA); write_data(0x00); write_data(0x00);
    
    write_command(0xC0); write_data(0x23); // Power control VRH
    write_command(0xC1); write_data(0x10); // Power control SAP
    write_command(0xC5); write_data(0x3E); write_data(0x28); // VCM control
    write_command(0xC7); write_data(0x86); // VCM control2
    
    write_command(0x36); write_data(0x28); // Memory Access Control (Landscape, MV, BGR)
    write_command(0x3A); write_data(0x55); // Pixel format (16-bit)
    
    write_command(0xB1); write_data(0x00); write_data(0x18);
    write_command(0xB6); write_data(0x08); write_data(0x82); write_data(0x27);
    
    write_command(0x11); // Sleep out
    usleep(150000);

    write_command(0x29); // Display ON
    usleep(50000);

    // 5. Draw Image Line-by-Line (Avoids CS hardware toggling issues)
    uint8_t *img_buf = malloc(WIDTH * HEIGHT * 2);
    memset(img_buf, 0, WIDTH * HEIGHT * 2); // default black
    
    int img_fd = open(argv[1], O_RDONLY);
    if (img_fd > 0) {
        read(img_fd, img_buf, WIDTH * HEIGHT * 2);
        close(img_fd);
    }
    
    for (int y = 0; y < HEIGHT; y++) {
        // ILI9341 with MADCTL 0x28 (Landscape) maps 0x2A to X (0-319) and 0x2B to Y (0-239)
        write_command(0x2A); // Column Set (X axis)
        uint8_t col_data[4] = {0x00, 0x00, (WIDTH-1) >> 8, (WIDTH-1) & 0xFF};
        write_data_buf(col_data, 4);
        
        write_command(0x2B); // Page Set (Y axis)
        uint8_t page_data[4] = {y >> 8, y & 0xFF, y >> 8, y & 0xFF};
        write_data_buf(page_data, 4);
        
        write_command(0x2C); // Memory Write
        
        // Write exactly 1 row (320 pixels * 2 bytes = 640 bytes)
        write_data_buf(img_buf + (y * WIDTH * 2), WIDTH * 2);
    }
    
    free(img_buf);
    close(spi_fd);
    return 0;
}
