import RPi.GPIO as GPIO
import time

# Use BCM GPIO numbering
GPIO.setmode(GPIO.BCM)

# Define pins
INPUT_PIN = 16
OUTPUT_PIN = 21

# Set up the input pin with a pull-down resistor so it stays LOW by default
GPIO.setup(INPUT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# Set up the output pin and default to LOW
GPIO.setup(OUTPUT_PIN, GPIO.OUT)
GPIO.output(OUTPUT_PIN, GPIO.LOW)

print(f"Listening on GPIO {INPUT_PIN} for a HIGH signal...")
print("Press Ctrl+C to exit.")

try:
    while True:
        # Check if the input pin is HIGH
        if GPIO.input(INPUT_PIN) == GPIO.HIGH:
            print(f"Signal detected on GPIO {INPUT_PIN}! Setting GPIO {OUTPUT_PIN} HIGH for 2 seconds.")
            
            # Set output to HIGH
            GPIO.output(OUTPUT_PIN, GPIO.HIGH)
            
            # Keep it HIGH for 2 seconds
            time.sleep(2)
            
            # Set output back to LOW
            GPIO.output(OUTPUT_PIN, GPIO.LOW)
            print(f"GPIO {OUTPUT_PIN} is back to LOW. Waiting for next signal...")
            
            # Small debounce delay to prevent rapid consecutive triggers if button is held
            time.sleep(0.5)
            
        # Small sleep to reduce CPU usage while waiting
        time.sleep(0.05)

except KeyboardInterrupt:
    print("\nTest interrupted. Cleaning up...")
finally:
    # Reset GPIO settings
    GPIO.cleanup()
