import pyaudio
import time


def audio_player(audio_queue, playback_activity, gui_queue, sample_rate=44100):
    audio = audio_queue.get()
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=sample_rate,
                    output=True)

    stream.write(audio.tobytes())
    stream.stop_stream()
    stream.close()
    p.terminate()


def audio_player2(audio_queue, playback_activity, gui_queue):
    # Initialize PyAudio
    p = pyaudio.PyAudio()

    while True:
        audio = audio_queue.get()
        if audio is None:
            break
        try:
            # GUI
            gui_queue.put({'type': 'status', 'value': "Speaking"})
            gui_queue.put({'type': 'circle', 'value': 'green'})

            # Open the audio stream
            playback_stream = p.open(format=pyaudio.paInt32,  # Assuming 16-bit PCM
                                     channels=audio.channels,  # Mono audio
                                     rate=audio.frame_rate,  # Sample rate
                                     output=True)

            playback_activity.value = True
            playback_stream.write(audio.raw_data)

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