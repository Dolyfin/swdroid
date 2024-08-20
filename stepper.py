import RPi.GPIO as GPIO
import time

# motor 1 pins
m1int1 = 17
m1in2 = 18
m1in3 = 27
m1in4 = 22

# motor 2 pins
m2in1 = 5
m2in2 = 6
m2in3 = 13
m2in4 = 19

step_count = 4096  # 5.625*(1/64) per step, 4096 steps is 360°

# defining stepper motor sequence (found in documentation http://www.4tronix.co.uk/arduino/Stepper-Motors.php)
step_sequence = [[1, 0, 0, 1],
                 [1, 0, 0, 0],
                 [1, 1, 0, 0],
                 [0, 1, 0, 0],
                 [0, 1, 1, 0],
                 [0, 0, 1, 0],
                 [0, 0, 1, 1],
                 [0, 0, 0, 1]]

# setting up
GPIO.setmode(GPIO.BCM)

m1_pins = [m1int1, m1in2, m1in3, m1in4]
m1_step_counter = 0

for pin in m1_pins:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)

m2_pins = [m2in1, m2in2, m2in3, m2in4]
m2_step_counter = 0

for pin in m2_pins:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)


def m1_move(steps=4096, delay=0.005, direction=True, freeze=False,):
    global m1_step_counter
    for i in range(steps):
        for pin in range(0, len(m1_pins)):
            GPIO.output(m1_pins[pin], step_sequence[m1_step_counter][pin])
        if direction == True:
            m1_step_counter = (m1_step_counter - 1) % 8
        elif direction == False:
            m1_step_counter = (m1_step_counter + 1) % 8
        time.sleep(delay)
    if freeze == False:
        for pin in m1_pins:
            GPIO.output(pin, GPIO.LOW)


def m2_move(steps=4096, delay=0.005, direction=True, freeze=False,):
    global m2_step_counter
    for i in range(steps):
        for pin in range(0, len(m2_pins)):
            GPIO.output(m2_pins[pin], step_sequence[m2_step_counter][pin])
        if direction == True:
            m2_step_counter = (m2_step_counter - 1) % 8
        elif direction == False:
            m2_step_counter = (m2_step_counter + 1) % 8
        time.sleep(delay)
    if freeze == False:
        for pin in m1_pins:
            GPIO.output(pin, GPIO.LOW)


def cleanup():
    for pin in m1_pins:
        GPIO.output(pin, GPIO.LOW)
    for pin in m2_pins:
        GPIO.output(pin, GPIO.LOW)
    GPIO.cleanup()
