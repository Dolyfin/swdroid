import time
import math
import asyncio

try:
    # checks if you have access to RPi.GPIO, which is available inside RPi
    import RPi.GPIO as GPIO

    RPI = True
except:
    # In case of exception, you are executing your script outside of RPi, so import Mock.GPIO
    import Mock.GPIO as GPIO

    RPI = False

# speaker pin
speaker1 = 12

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

m1_pins = [m1int1, m1in2, m1in3, m1in4]
m1_step_counter = 0

m2_pins = [m2in1, m2in2, m2in3, m2in4]
m2_step_counter = 0

m1_last = 0
m2_last = 0


# Motor 1 movement
async def m1_move(steps: int = 4096, delay: float = 0.001, freeze: bool = False):
    global m1_step_counter

    direction = True
    if steps < 0:
        steps = steps * -1
        direction = False

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


# Motor 2 movement
async def m2_move(steps: int = 4096, delay: float = 0.001, freeze: bool = False):
    global m2_step_counter

    direction = True
    if steps < 0:
        steps = steps * -1
        direction = False

    for i in range(steps):
        for pin in range(0, len(m2_pins)):
            GPIO.output(m2_pins[pin], step_sequence[m2_step_counter][pin])
        if direction == True:
            m2_step_counter = (m2_step_counter - 1) % 8
        elif direction == False:
            m2_step_counter = (m2_step_counter + 1) % 8
        time.sleep(delay)
    if freeze == False:
        for pin in m2_pins:
            GPIO.output(pin, GPIO.LOW)


async def motor_move_to(freq):
    global m1_last, m2_last

    m1_steps = freq - 550
    m2_steps = m1_steps * -1

    m1_steps = round(m1_steps * 0.3)
    m2_steps = round(m2_steps * 0.3)

    m1_steps -= m1_last
    m2_steps -= m2_last

    # Move both motors concurrently and update last step values
    await asyncio.gather(
        m1_move(steps=m1_steps),
        m2_move(steps=m2_steps)
    )

    # Store the last known positions
    m1_last = m1_steps
    m2_last = m2_steps

    print(f"m1:{m1_last}  m2:{m2_last}")


def fnv1a_hash(word):
    h = 2166136261
    for c in word:
        h ^= ord(c)
        h *= 16777619
        h &= 0xFFFFFFFF
    return h


def generate_beep(frequency, pwm, duration=0.1, amplitude=0.05):
    # Set the PWM frequency to the desired beep frequency
    pwm.ChangeFrequency(frequency)
    pwm.start(amplitude * 100)  # Start with 0% duty cycle
    time.sleep(duration)
    pwm.stop()  # Stop the beep


def word_to_beeps(word, factor=3, min_freq=200, max_freq=900):
    punctuation_freq = -1
    punctuation = {
        "!": 800,
        "?": 500,
        "...": 300,
        ".": 400
    }
    for key in punctuation:
        if word.endswith(key):
            punctuation_freq = punctuation[key]
            break

    # Normalize the word: lowercase and remove punctuation
    normalized_word = ''.join(char for char in word.lower() if char.isalnum())

    # Calculate the number of beeps based on word length
    num_beeps = math.ceil(len(normalized_word) / factor)

    # Use FNV-1a hash
    hash_int = fnv1a_hash(normalized_word)

    # Generate the frequencies
    freqs = []
    for i in range(num_beeps):
        segment = (hash_int >> (i * 8)) & 0xFF
        freq = min_freq + (segment / 255) * (max_freq - min_freq)
        freq = round(freq)  # rounds into nice numbers to work with
        print(f"f:{freq}")
        freqs.append(freq)

    if punctuation_freq > 0:
        freqs.append(punctuation_freq)

    return freqs


async def droid_action(sentence, pwm):
    words = sentence.split()

    for word in words:
        freqs = word_to_beeps(word)

        for freq in freqs:
            print(f"m:{freq}")
            await asyncio.create_task(motor_move_to(freq))
            generate_beep(freq, pwm)
        await asyncio.sleep(0.05)


async def gpio_control(response_text_queue, playback_activity, gui_queue):
    if RPI:
        print("RPI.GPIO detected.")
    else:
        print("RPI.GPIO not detected. falling back to Mock.GPIO")

    # setting up
    GPIO.setmode(GPIO.BCM)

    # Speaker GPIO setup
    GPIO.setup(speaker1, GPIO.OUT)

    # Set up PWM on the GPIO pin
    pwm = GPIO.PWM(speaker1, 200)  # placeholder frequency

    # Motor GPIO setup
    for pin in m1_pins:
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, GPIO.LOW)

    for pin in m2_pins:
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, GPIO.LOW)

    while True:
        response_text = response_text_queue.get()

        # GUI
        gui_queue.put({'type': 'status', 'value': "Speaking"})
        gui_queue.put({'type': 'circle', 'value': 'green'})

        playback_activity.value = True
        await droid_action(response_text, pwm)
        playback_activity.value = False

        if response_text_queue.empty():
            # GUI
            gui_queue.put({'type': 'status', 'value': "Idle"})
            gui_queue.put({'type': 'circle', 'value': 'grey'})
        else:
            # GUI
            gui_queue.put({'type': 'status', 'value': "Speaking"})
            gui_queue.put({'type': 'circle', 'value': 'PaleGreen4'})

        time.sleep(0.2)


def main(response_text_queue, playback_activity, gui_queue):
    asyncio.run(gpio_control(response_text_queue, playback_activity, gui_queue))