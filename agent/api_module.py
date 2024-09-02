import io
import wave
import numpy
import requests
import time
from faster_whisper import WhisperModel
from llama_cpp import Llama
from styletts2 import tts
import os

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

stt_model_name = "base.en"
llm_model_link = "https://huggingface.co/ThomasBaruzier/gemma-2-2b-it-GGUF/resolve/main/gemma-2-2b-it-Q4_0_4_4.gguf"
llm_model_name = "gemma-2-2b-it-Q4_0_4_4.gguf"
models_dir = "models"


def initialize():
    global llm, whisper
    # Ensure the models directory exists
    os.makedirs(models_dir, exist_ok=True)

    # Full path to the model file
    model_path = os.path.join(models_dir, llm_model_name)

    # Check if the model file already exists
    if not os.path.exists(model_path):
        print(f"Model not found. Downloading {llm_model_name}...")

        # Download the file
        response = requests.get(llm_model_link, stream=True)
        if response.status_code == 200:
            with open(model_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"Downloaded {llm_model_name} successfully.")
        else:
            print(f"Failed to download the model. Status code: {response.status_code}")
    else:
        print(f"Model {llm_model_name} is already downloaded.")

    llm = Llama(
        model_path=os.path.join(models_dir, llm_model_name),
        n_ctx=2048,
        n_thread=1,
    )
    print(f"LLM loaded! ({llm_model_name})")

    whisper = WhisperModel(model_size_or_path=stt_model_name, device="cpu", compute_type="int8", cpu_threads=3,
                           download_root=os.path.join(os.getcwd(), models_dir))
    print(f"STT loaded! ({stt_model_name})")


def initialize_tts():
    import nltk
    nltk.download('punkt_tab')

    global styletts

    styletts = tts.StyleTTS2()
    print(f"TTS loaded! (StyleTTS2)")


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

            segments, info = whisper.transcribe(audio_buffer, beam_size=5)

            print("Detected language '%s' with probability %f" % (info.language, info.language_probability))

            for segment in segments:
                full_text = segment.text

        time_taken_ms = round((time.time() - start_time) * 1000, 1)
        print(f"Whisper API:{time_taken_ms}ms")
        gui_queue.put({'type': 'stt_latency', 'value': time_taken_ms})

        return full_text
    except Exception as e:
        print(f"Exception during transcription: {e}")
        return "ERROR: API"


def llm_api_request(gui_queue, llm_prompt='', stop_tokens=None):
    try:
        start_time = time.time()
        output = llm(
            prompt=llm_prompt,
            max_tokens=64,
            stop=stop_tokens,
            echo=False
        )

        time_taken_ms = round((time.time() - start_time) * 1000, 1)
        print(f"Text API:{time_taken_ms}ms")
        gui_queue.put({'type': 'llm_latency', 'value': time_taken_ms})

        return output['choices'][0]['text']
    except Exception as e:
        print(f"Exception during LLM generation: {e}")
        return "ERROR: API"


def tts_api_request(gui_queue, tts_prompt=''):
    start_time = time.time()

    output = styletts.inference(
        text=tts_prompt,
        target_voice_path=None,
        output_wav_file=None,
        output_sample_rate=24000,
        alpha=0.3,
        beta=0.7,
        diffusion_steps=5,
        embedding_scale=1,
        ref_s=None)

    time_taken_ms = round((time.time() - start_time) * 1000, 1)
    print(f"Speech API:{time_taken_ms}ms")
    gui_queue.put({'type': 'tts_latency', 'value': time_taken_ms})
    return output
