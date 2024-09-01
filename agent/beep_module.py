import time
import math
import numpy as np
import pyaudio
try:
    # checks if you have access to RPi.GPIO, which is available inside RPi
    import RPi.GPIO as GPIO
    RPI = True
except:
    # In case of exception, you are executing your script outside of RPi, so import Mock.GPIO
    import Mock.GPIO as GPIO
    RPI = False


def fnv1a_hash(word):
    h = 2166136261
    for c in word:
        h ^= ord(c)
        h *= 16777619
        h &= 0xFFFFFFFF
    return h


def generate_beep(frequency, pwm, duration=0.1, sample_rate=44100, amplitude=0.05):
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


def droid_speak(sentence, pwm):
    words = sentence.split()

    for word in words:
        freqs = word_to_beeps(word)

        for freq in freqs:
                generate_beep(freq, pwm)
                # play_sound(beep)
        time.sleep(0.05)


def main(response_text_queue, playback_activity, gui_queue):
    # GPIO setup
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(12, GPIO.OUT)

    # Set up PWM on the GPIO pin
    pwm = GPIO.PWM(12, 100)  # 440Hz is a placeholder frequency

    if RPI:
        print("RPI.GPIO detected.")
    else:
        print("RPI.GPIO not detected. falling back to Mock.GPIO")

    while True:
        response_text = response_text_queue.get()

        # GUI
        gui_queue.put({'type': 'status', 'value': "Speaking"})
        gui_queue.put({'type': 'circle', 'value': 'green'})

        playback_activity.value = True
        droid_speak(response_text, pwm)
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
