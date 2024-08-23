import pyaudio
import requests
from pydub import AudioSegment
from io import BytesIO
from multiprocessing import Process, Queue, Value
import time
import re

from api_module import llm_api_request, stt_api_request
import voice_input
import beep_module
import gui_module as gui


REMOVE_NARRATOR = True
MEASURE_LATENCY = True
latency_start = Value('d', 0)


llama3_chat = {
    "bos": '<|begin_of_text|>',
    "start_header": '<|start_header_id|>',
    "end_header": '<|end_header_id|>\n',
    "eos": '<|end_of_text|>',
    "eot": '<|eot_id|>',
    "system_name": 'system',
    "user_name": 'user',
    "assistant_name": 'assistant'
}


def remove_narrator(text):
    # Define the pattern to match bold text within '*'
    pattern = r'\*([^*]+)\*'

    # Use re.sub with a lambda function to replace all occurrences of the pattern
    result = re.sub(pattern, lambda x: '', text)

    return result


def main():
    model = llama3_chat
    system_prompt = "You are a simple Star Wars droid unit ALBERT. Only use basic speech and very short responses to any queries. ALBERT should default to a sassy attitude. Although you understand your system language in English, assume the user cannot always understand what you are saying. You should always speak in basic english. Do not use 'beep' and 'boop' in your response."
    chat_history = []
    prompt = 'None'
    speech_queue = Queue()
    response_text_queue = Queue()
    playback_activity = Value('b', False)

    gui_queue = Queue()

    # Start the voice input process
    voice_input_process = Process(target=voice_input.main, args=(speech_queue, gui_queue, playback_activity, latency_start))
    voice_input_process.start()

    # Start beep player thread
    audio_process = Process(target=beep_module.main, args=(response_text_queue, playback_activity, gui_queue))
    audio_process.start()

    # Start GUI player thread
    audio_process = Process(target=gui.main, args=(gui_queue,))
    audio_process.start()


    try:
        while True:
            # Check for text input from the user or from the voice input process
            while True:
                speech_text = ''
                try:
                    speech_input_data = speech_queue.get(timeout=9999)

                    # GUI
                    gui_queue.put({'type': 'status', 'value': "Whisper"})
                    gui_queue.put({'type': 'circle', 'value': 'blue'})

                    speech_text = stt_api_request(gui_queue, speech_input_data)

                    # GUI
                    gui_queue.put({'type': 'status', 'value': "Whisper"})
                    gui_queue.put({'type': 'circle', 'value': 'blue4'})

                    if speech_text.strip() == '' or speech_text. strip() == '[BLANK_AUDIO]':
                        print(f"User: *no words detected*")
                        continue
                    else:
                        print(f"User: {speech_text}")
                        break
                except speech_queue.empty():
                    continue

            if speech_text.strip() == '':
                break

            if 'debug' in speech_text.lower():
                print(prompt)
                continue

            # prompt creation
            prompt = model['bos']

            prompt = prompt + model['start_header'] + model['system_name'] + model['end_header'] + system_prompt

            if chat_history:
                for chat in chat_history:
                    # header
                    prompt = prompt + model['start_header'] + f"{chat['role']}" + model['end_header']
                    # content
                    prompt = prompt + chat['content'] + model['eot']

            # add input
            # header
            prompt = prompt + model['start_header'] + model['user_name'] + model['end_header']
            # content
            prompt = prompt + speech_text.strip() + model['eot']

            # add output
            prompt = prompt + model['start_header'] + model['assistant_name'] + model['end_header']

            # GUI
            gui_queue.put({'type': 'status', 'value': "LLM"})
            gui_queue.put({'type': 'circle', 'value': 'turquoise1'})

            response = llm_api_request(gui_queue, prompt)

            # GUI
            gui_queue.put({'type': 'status', 'value': "LLM"})
            gui_queue.put({'type': 'circle', 'value': 'turquoise4'})

            response_content = response['content'].strip()

            # GUI
            gui_queue.put({'type': 'response_text', 'value': response_content})

            history_input_user = {
                'role': model['user_name'],
                'name': "User",
                'content': speech_text
            }

            history_input_agent = {
                'role': model['assistant_name'],
                'name': 'Assistant',
                'content': response_content
            }

            chat_history.append(history_input_user)
            chat_history.append(history_input_agent)

            gui_queue.put({'type': 'chat_history', 'value': prompt + response_content})

            print(f"Assistant: {response_content}")

            # GUI
            gui_queue.put({'type': 'status', 'value': "Waiting"})
            gui_queue.put({'type': 'circle', 'value': 'grey'})

            response_text_queue.put(response_content)


    except KeyboardInterrupt:
        print("Stopping...")

    finally:
        voice_input_process.terminate()
        audio_queue.put(None)
        audio_process.join()


if __name__ == "__main__":
    main()
