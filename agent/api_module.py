import io
import wave
import numpy
import requests
import time
from faster_whisper import WhisperModel
from llama_cpp import Llama
import os

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

STT_MODEL_NAME = "base.en"
LLM_MODEL_LINK = "https://huggingface.co/ThomasBaruzier/gemma-2-2b-it-GGUF/resolve/main/gemma-2-2b-it-Q4_0_4_4.gguf"
LLM_MODEL_NAME = "gemma-2-2b-it-Q4_0_4_4.gguf"
TTS_MODEL_LINK = "https://models.silero.ai/models/tts/en/v3_en.pt"
TTS_MODEL_NAME = "v3_en.pt"
MODELS_DIR = "models"


def initialize():
    global llm, whisper
    # Ensure the models directory exists
    os.makedirs(MODELS_DIR, exist_ok=True)

    # Full path to the model file
    model_path = os.path.join(MODELS_DIR, LLM_MODEL_NAME)

    # Check if the model file already exists
    if not os.path.exists(model_path):
        print(f"Model not found. Downloading {LLM_MODEL_NAME}...")

        # Download the file
        response = requests.get(LLM_MODEL_LINK, stream=True)
        if response.status_code == 200:
            with open(model_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"Downloaded {LLM_MODEL_NAME} successfully.")
        else:
            print(f"Failed to download the model. Status code: {response.status_code}")
    else:
        print(f"Model {LLM_MODEL_NAME} is already downloaded.")

    llm = Llama(
        model_path=os.path.join(MODELS_DIR, LLM_MODEL_NAME),
        n_ctx=2048,
        n_thread=2,
    )
    print(f"LLM loaded! ({LLM_MODEL_NAME})")

    whisper = WhisperModel(model_size_or_path=STT_MODEL_NAME, device="cpu", compute_type="int8", cpu_threads=3,
                           download_root=os.path.join(os.getcwd(), MODELS_DIR))
    print(f"STT loaded! ({STT_MODEL_NAME})")


# def initialize_tts():
#     print(f"Loading TTS... (SileroTTS)")
#
#     device = torch.device('cpu')
#     torch.set_num_threads(4)
#     local_file = os.path.join(MODELS_DIR, TTS_MODEL_NAME)
#
#     if not os.path.isfile(local_file):
#         print(f"Downloading TTS Model: {TTS_MODEL_LINK}")
#         torch.hub.download_url_to_file(url=TTS_MODEL_LINK,
#                                        dst=local_file)
#
#     tts_model = torch.package.PackageImporter(local_file).load_pickle("tts_models", "model")
#     tts_model.to(device)
#
#     print(f"TTS loaded! (SileroTTS)")


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


# def tts_api_request(gui_queue, tts_prompt='Hello world!'):
#     start_time = time.time()
#
#     time_taken_ms = round((time.time() - start_time) * 1000, 1)
#     print(f"Speech API:{time_taken_ms}ms")
#     gui_queue.put({'type': 'tts_latency', 'value': time_taken_ms})
#     return
