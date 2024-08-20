import RPi.GPIO as GPIO
import wave
import pyaudio
import time

# Setup GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(20, GPIO.OUT)

# Open the WAV file
wav_file = wave.open('test.wav', 'rb')

# Set up PyAudio
p = pyaudio.PyAudio()
stream = p.open(format=p.get_format_from_width(wav_file.getsampwidth()),
                channels=1,  # Mono
                rate=wav_file.getframerate(),
                output=True)

# Create a PWM instance on GPIO 20
pwm = GPIO.PWM(20, wav_file.getframerate())  # PWM frequency set to sample rate
pwm.start(0)  # Start PWM with a duty cycle of 0

# Play the audio file
data = wav_file.readframes(1024)
while len(data) > 0:
    # Convert the audio data to PWM duty cycle (range from 0 to 100)
    for sample in data:
        duty_cycle = sample / 255.0 * 100  # Convert sample to duty cycle percentage
        pwm.ChangeDutyCycle(duty_cycle)
        time.sleep(1.0 / wav_file.getframerate())  # Wait for one sample period

    data = wav_file.readframes(1024)

# Cleanup
stream.stop_stream()
stream.close()
p.terminate()
pwm.stop()
GPIO.cleanup()

print("Playback finished.")
