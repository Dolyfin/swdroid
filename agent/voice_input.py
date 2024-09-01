import os
import wave
import pyaudio
import threading
import queue
import time
from pysilero_vad import SileroVoiceActivityDetector
import numpy
from collections import deque
from multiprocessing import Queue, Value

# test options
input_loopback = False
dump_audio = False
mute_while_speaking = True

# Global variables to keep track of VAD state
speech_active = False
silence_counter = 0
speech_audio_list = []


# class PlaybackActivity:
#     def __init__(self):
#         self.playback_activity = False
#
#     def true(self):
#         self.playback_activity = True
#
#     def false(self):
#         self.playback_activity = False
#
#     def get(self):
#         return self.playback_activity


class SpeechAudioBuffer:
    def __init__(self):
        self.buffer = []

    def add_chunk(self, chunk):
        self.buffer.append(chunk)

    def get_buffer(self):
        return self.buffer

    def clear_buffer(self):
        self.buffer = []


def silero_vad_process(vad, audio_chunk, vad_threshold=0.7):
    start_time = time.perf_counter()
    if vad(audio_chunk) >= vad_threshold:
        # print(f"VAD: TRUE : {round((time.perf_counter() - start_time) * 1000,2)}")
        return True
    # print(f"VAD: FALSE: {round((time.perf_counter() - start_time) * 1000,2)}")
    return False


def save_audio_to_wav(audio_chunks, filename, format=pyaudio.paInt16, channels=1, rate=16000):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    wf = wave.open(filename, 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(pyaudio.PyAudio().get_sample_size(format))
    wf.setframerate(rate)
    wf.writeframes(b''.join(audio_chunks))
    wf.close()


def adjust_volume(audio_chunk, volume_gain):
    # Convert audio chunk to numpy array
    audio_data = numpy.frombuffer(audio_chunk, dtype=numpy.int16)
    # Apply volume gain
    audio_data = numpy.clip(audio_data * volume_gain, -32768, 32767).astype(numpy.int16)
    # Convert back to bytes
    return audio_data.tobytes()


def audio_capture(audio_queue,
                  gui_queue,
                  playback_activity,
                  format=pyaudio.paInt16,
                  channels=1,
                  chunk_size=16000,
                  rate=16000):
    # global pa
    try:

        pa = pyaudio.PyAudio()
        stream = pa.open(format=format,
                         channels=channels,
                         rate=rate,
                         input=True,
                         frames_per_buffer=chunk_size)

        if input_loopback is True:
            output_stream = pa.open(format=format,
                                    channels=channels,
                                    rate=rate,
                                    output=True)

        while True:
            data = stream.read(chunk_size)

            # stops recording if there is playback
            if (playback_activity.value == 0 and mute_while_speaking is True) or mute_while_speaking is False:
                audio_queue.put(data)

            if input_loopback is True:
                output_stream.write(data)
    except:
        stream.stop_stream()
        stream.close()
        output_stream.stop_stream()
        output_stream.close()
        pa.terminate()


def phrase_detection(gui_queue,
                     vad_result,
                     audio_chunk,
                     speech_audio_buffer,
                     latency_start,
                     gap_max_chunks=10):
    global speech_active, silence_counter, speech_audio_list

    if vad_result is False and speech_active is False:
        speech_audio_buffer.clear_buffer()
    speech_audio_buffer.add_chunk(audio_chunk)

    if vad_result is True:
        if speech_active is False:
            print(f'Speech starting')
            speech_active = True

            # GUI
            gui_queue.put({'type': 'status', 'value': "Listening"})
            gui_queue.put({'type': 'circle', 'value': 'red'})
        silence_counter = 0
    else:
        if speech_active is True:
            silence_counter += 1
            if silence_counter >= gap_max_chunks:
                print(f'Speech ended')
                # GUI
                gui_queue.put({'type': 'status', 'value': "Recorded"})
                gui_queue.put({'type': 'circle', 'value': 'red2'})

                latency_start.value = time.time()
                speech_active = False
                silence_counter = 0
                speech_output_array = speech_audio_buffer.get_buffer()
                speech_audio_buffer.clear_buffer()

                if dump_audio:
                    filename = f"debug/speech_{int(time.time())}.wav"
                    save_audio_to_wav(speech_output_array, filename)
                    print(f'Saved speech to {filename}')

                return speech_output_array
    return None


def main(speech_queue, gui_queue, playback_activity=False, latency_start=Value('d', 0)):
    vad = SileroVoiceActivityDetector()
    print("SileroVAD loaded!")

    audio_queue = queue.Queue()
    channels = 1
    chunk_size = 960  # 480 (30ms) 960 (60ms) 1600 (100ms)
    samplerate = 16000

    gap_max_chunks = 16

    volume_gain = 3

    speech_audio_buffer = SpeechAudioBuffer()

    # Start the audio capture thread
    audio_thread = threading.Thread(target=audio_capture, args=(
        audio_queue, gui_queue, playback_activity, pyaudio.paInt16, channels, chunk_size, samplerate))
    audio_thread.daemon = True
    audio_thread.start()
    print("Ready!")

    try:
        while True:
            try:
                # Wait for an audio chunk with a timeout to allow graceful shutdown
                audio_chunk = audio_queue.get(timeout=1)

                audio_chunk = adjust_volume(audio_chunk, volume_gain)

                vad_result = silero_vad_process(vad, audio_chunk)
                speech_output = phrase_detection(gui_queue, vad_result, audio_chunk, speech_audio_buffer, latency_start,
                                                 gap_max_chunks)
                if speech_output is not None:
                    speech_queue.put(speech_output)
            except queue.Empty:
                continue
    except KeyboardInterrupt:
        print("Stopping...")


if __name__ == "__main__":
    main(speech_queue=Queue(), gui_queue=Queue())
