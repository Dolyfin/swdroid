import time
import pigpio

# Initialize pigpio and set up the GPIO pin
pi = pigpio.pi()

if not pi.connected:
    exit()

GPIO_PIN = 12


def generate_beep(frequency):
    pi.hardware_PWM(GPIO_PIN, frequency, 500000)  # 50% duty cycle (500,000 out of 1,000,000)
    time.sleep(1)  # Play the beep for 1 second
    pi.hardware_PWM(GPIO_PIN, 0, 0)  # Stop the PWM signal


def main():
    try:
        while True:
            freq = float(input("Enter frequency (Hz): "))
            print(f"Playing beep at {freq} Hz for 1 second...")
            generate_beep(freq)

            cont = input("Play another beep? (y/n): ")
            if cont.lower() != 'y':
                break
    except KeyboardInterrupt:
        pass
    finally:
        pi.set_mode(GPIO_PIN, pigpio.INPUT)  # Reset GPIO pin
        pi.stop()
        print("Exiting...")


if __name__ == "__main__":
    main()
