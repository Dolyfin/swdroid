import io
import wave
import numpy
import requests
import time

llm_api = 'http://192.168.0.99:7701'
tts_api = 'http://192.168.0.99:7851'
stt_api = 'http://192.168.0.99:7700'


def llm_api_request(gui_queue, llm_prompt=''):
    start_time = time.time()
    response = requests.post(
        f"{llm_api}/completion",
        headers={"Content-Type": "application/json"},
        json={
            "prompt": llm_prompt,
            "n_predict": 1024,
            "stop": ['<|end|>', '<|user|>', '<|assistant|>', '\n\n']
        }
    )

    response = response.json()
    time_taken_ms = round((time.time() - start_time) * 1000, 1)

    # print(response)
    # print(response['content'])
    # print(f"Context TPS:{round(response['timings']['prompt_per_second'],1)}")
    # print(f"Predicted TPS:{round(response['timings']['predicted_per_second'],1)}")
    print(f"Text API:{time_taken_ms}ms")
    gui_queue.put({'type': 'llm_latency', 'value': time_taken_ms})
    return response


def stt_api_request(gui_queue, audio_data, channels=1, samplerate=16000):
    start_time = time.time()
    full_text = 'none'

    try:
        if isinstance(audio_data, list):
            if not audio_data:
                raise ValueError("audio_data list is empty")

            # Ensure all elements are one-dimensional arrays
            audio_data = [numpy.atleast_1d(chunk) for chunk in audio_data]
            audio_data = numpy.concatenate(audio_data)

        # Use an in-memory buffer to hold the audio data
        with io.BytesIO() as audio_buffer:
            # Write audio data to the buffer in WAV format
            with wave.open(audio_buffer, 'wb') as wav_file:
                wav_file.setnchannels(channels)
                wav_file.setsampwidth(2)  # 2 bytes for int16
                wav_file.setframerate(samplerate)
                wav_file.writeframes(audio_data.tobytes())

            # Rewind the buffer to the beginning, so it can be read from
            audio_buffer.seek(0)

            # Send the in-memory buffer to the Whisper API
            response = requests.post(
                f"{stt_api}/inference",
                files={"file": ("temp.wav", audio_buffer, "audio/wav")},
                data={"temperature": "0.0", "temperature_inc": "0.2", "response_format": "json"}
            )

        time_taken_ms = round((time.time() - start_time) * 1000, 1)
        print(f"Whisper API:{time_taken_ms}ms")
        gui_queue.put({'type': 'stt_latency', 'value': time_taken_ms})
        # Handle the response
        if response.status_code == 200:
            response_json = response.json()
            full_text = response_json.get("text", "").strip()
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return f"ERROR: API {response.status_code}"
    except Exception as e:
        print(f"Exception during transcription: {e}")
        return "ERROR: API"
    return full_text

