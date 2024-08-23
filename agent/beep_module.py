import time
import math
import numpy as np
import pyaudio
import RPi.GPIO as GPIO

PLAY_PCM = True

# GPIO setup
GPIO.setmode(GPIO.BCM)
GPIO.setup(12, GPIO.OUT)

# Set up PWM on the GPIO pin
pwm = GPIO.PWM(12, 100)  # 440Hz is a placeholder frequency

if not PLAY_PCM:
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16,
                channels=1,
                rate=44100,
                output=True)


def fnv1a_hash(word):
    h = 2166136261
    for c in word:
        h ^= ord(c)
        h *= 16777619
        h &= 0xFFFFFFFF
    return h


def generate_beep(frequency, duration=0.1, sample_rate=44100, amplitude=0.7):
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    wave = amplitude * np.sin(2 * np.pi * frequency * t)

    # Apply fade-in and fade-out
    fade_duration = int(sample_rate * 0.01)  # 10ms fade in/out
    fade_in = np.linspace(0, 1, fade_duration)
    fade_out = np.linspace(1, 0, fade_duration)
    wave[:fade_duration] *= fade_in
    wave[-fade_duration:] *= fade_out

    # Ensure waveform is in 16-bit range
    wave = np.int16(wave * 32767)

    return wave


def generate_beep_pwm(frequency, duration=0.1, sample_rate=44100, amplitude=0.3):
    print('hi')
    # Set the PWM frequency to the desired beep frequency
    pwm.ChangeFrequency(frequency)
    pwm.start(30)  # Start with 0% duty cycle
    time.sleep(duration)
    pwm.stop()  # Stop the beep


def play_sound(sound_wave):
    if not PLAY_PCM:
        stream.write(sound_wave.tobytes())


def add_silence(duration=0.05, sample_rate=44100):
    num_samples = int(duration * sample_rate)
    silence = np.zeros(num_samples, dtype=np.int16)
    play_sound(silence)


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


def droid_speak(sentence):
    words = sentence.split()

    # Start with a short silence to stabilize
    add_silence(0.05)

    for word in words:
        freqs = word_to_beeps(word)

        for freq in freqs:
            if PLAY_PCM:
                generate_beep_pwm(freq)
            else:
                beep = generate_beep(freq)
                play_sound(beep)
        time.sleep(0.05)

    # Add a short silence at the end
    add_silence(0.1)


def main(response_text_queue, playback_activity, gui_queue):
    while True:
        response_text = response_text_queue.get()

        # GUI
        gui_queue.put({'type': 'status', 'value': "Speaking"})
        gui_queue.put({'type': 'circle', 'value': 'green'})

        playback_activity.value = True
        droid_speak(response_text)
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


# Make sure to stop the stream gracefully
def close_stream():
    stream.stop_stream()
    stream.close()
    p.terminate()


# Make sure to close the stream when done
import atexit
atexit.register(close_stream)
