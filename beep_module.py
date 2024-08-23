import time
import math
import numpy as np
import simpleaudio as sa
import pyaudio


def fnv1a_hash(word):
    h = 2166136261
    for c in word:
        h ^= ord(c)
        h *= 16777619
        h &= 0xFFFFFFFF
    return h


def generate_beep(frequency, duration=0.05, sample_rate=44100, amplitude=0.5):
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    wave = amplitude * np.sin(2 * np.pi * frequency * t)

    # Apply fade-in and fade-out
    fade_duration = int(sample_rate * 0.02)  # 50ms fade in/out
    fade_in = np.linspace(0, 1, fade_duration)
    fade_out = np.linspace(1, 0, fade_duration)
    wave[:fade_duration] *= fade_in
    wave[-fade_duration:] *= fade_out

    # Ensure waveform is in 16-bit range
    wave = np.int16(wave * 32767)

    return wave


def play_sound(sound_wave, sample_rate=44100):
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=sample_rate,
                    output=True)

    stream.write(sound_wave.tobytes())
    stream.stop_stream()
    stream.close()
    p.terminate()


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

    for word in words:
        freqs = word_to_beeps(word)

        for freq in freqs:
            beep = generate_beep(freq)
            play_sound(beep)
        time.sleep(0.05)