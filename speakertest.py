import time
import RPi.GPIO as GPIO

# GPIO setup
GPIO.setmode(GPIO.BCM)
GPIO.setup(12, GPIO.OUT)

# Set up PWM on the GPIO pin
pwm = GPIO.PWM(12, 500)  # 440Hz is a placeholder frequency


def generate_beep(frequency):
    pwm.ChangeFrequency(frequency)
    pwm.start(50)  # 50% duty cycle for a simple square wave
    time.sleep(1)  # Play the beep for 1 second
    pwm.stop()


def main():
    try:
        while True:
            freq = float(input("Enter frequency (Hz): "))
            print(f"Playing beep at {freq} Hz for 1 second...")
            generate_beep(freq)
    except KeyboardInterrupt:
        pass
    finally:
        pwm.stop()
        GPIO.cleanup()
        print("Exiting...")


if __name__ == "__main__":
    main()
