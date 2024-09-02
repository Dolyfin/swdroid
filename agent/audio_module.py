import pyaudio
import numpy as np
import time

def audio_player(audio_queue, playback_activity, gui_queue):
    p = pyaudio.PyAudio()

    while True:
        audio = audio_queue.get()
        if audio is None:
            break
        try:
            # GUI
            gui_queue.put({'type': 'status', 'value': "Speaking"})
            gui_queue.put({'type': 'circle', 'value': 'green'})

            # Assuming audio is a NumPy ndarray with raw PCM data
            playback_stream = p.open(format=pyaudio.paFloat32,  # Assuming 16-bit PCM
                                     channels=1,  # Mono audio
                                     rate=24000,  # Sample rate, assuming 24kHz
                                     output=True)

            playback_activity.value = True
            playback_stream.write(audio.tobytes())

            playback_stream.stop_stream()
            playback_stream.close()
            playback_activity.value = False

            if audio_queue.empty():
                # GUI
                gui_queue.put({'type': 'status', 'value': "Idle"})
                gui_queue.put({'type': 'circle', 'value': 'grey'})
            else:
                # GUI
                gui_queue.put({'type': 'status', 'value': "Speaking"})
                gui_queue.put({'type': 'circle', 'value': 'PaleGreen4'})
            time.sleep(0.3)
        except Exception as e:
            print(f"Error playing audio: {e}")
    p.terminate()
