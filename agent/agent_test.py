from multiprocessing import Process, Queue, Value
import re
import numpy as np
import torch
import os
import api_module
import voice_input
import gpio_module
import gui_module as gui
import audio_module


REMOVE_NARRATOR = False
latency_start = Value('d', 0)

BEEP = True

llama3_chat = {
    "bos": '<|begin_of_text|>',
    "start_header": '<|start_header_id|>',
    "end_header": '<|end_header_id|>\n',
    "eos": '',
    "eot": '<|eot_id|>',
    "system_name": 'system',
    "user_name": 'user',
    "assistant_name": 'assistant',
    "stop_tokens": ['<|end|>', '<|user|>', '<|assistant|>', '\n\n']
}

gemma2_chat = {
    "bos": '',
    "start_header": '<start_of_turn>',
    "end_header": '\n',
    "eos": '<end_of_turn>\n',
    "eot": '<end_of_turn>\n',
    "system_name": 'user',
    "user_name": 'user',
    "assistant_name": 'model',
    "stop_tokens": ['<end_of_turn>', '\n\n']
}


def remove_narrator(text):
    # Define the pattern to match bold text within '*'
    pattern = r'\*([^*]+)\*'

    # Use re.sub with a lambda function to replace all occurrences of the pattern
    result = re.sub(pattern, lambda x: '', text)

    return result


def tts_worker(tts_model, tts_queue, audio_queue, gui_queue):
    # api_module.initialize_tts()

    device = torch.device('cpu')
    torch.set_num_threads(4)
    local_file = '../v3_en.pt'

    if not os.path.isfile(local_file):
        torch.hub.download_url_to_file('https://models.silero.ai/models/tts/en/v3_en.pt',
                                       local_file)

    tts_model = torch.package.PackageImporter(local_file).load_pickle("tts_models", "model")
    tts_model.to(device)



    while True:
        text = tts_queue.get()
        print('tts queue read')
        print(f"tts: {text}")
        if text is None or text == '. .':
            break

        if REMOVE_NARRATOR is True:
            text = remove_narrator(text)

        # GUI
        gui_queue.put({'type': 'status', 'value': "StyleTTS"})
        gui_queue.put({'type': 'circle', 'value': 'yellow'})

        example_text = 'This is some sample text,'
        sample_rate = 24000
        speaker = 'en_0'
        tts_response = tts_model.apply_tts(text=example_text, speaker=speaker, sample_rate=sample_rate)

        print(tts_response)
        print(tts_response.dtype)
        print(f"Min value: {tts_response.min()}, Max value: {tts_response.max()}")
        print(type(tts_response))

        # GUI
        gui_queue.put({'type': 'status', 'value': "TTS done"})
        gui_queue.put({'type': 'circle', 'value': 'purple'})

        # convert audio into numpy array
        if isinstance(tts_response, torch.Tensor):
            print(f"Min value: {tts_response.min()}, Max value: {tts_response.max()}")
            tts_response = tts_response.detach().data.cpu().numpy()
            print(f"Min value: {tts_response.min()}, Max value: {tts_response.max()}")
            print(tts_response)

        # Assuming the ndarray is the raw audio data
        if isinstance(tts_response, np.ndarray):
            # Directly put the ndarray into the audio queue
            audio_queue.put(tts_response)

        else:
            print("Unexpected TTS response format.")


def main():
    api_module.initialize()

    model = gemma2_chat
    system_prompt = "You are a simple Star Wars droid unit ALBERT. Only use basic speech and very short responses to any queries. Although you understand your system language in English, assume the user cannot always understand what you are saying. You should always speak in basic english. Do not use 'beep' and 'boop' in your response."
    # system_prompt = "You are J.A.R.V.I.S. An advanced artificial intelligence who's purpose is to assist the user, Tony Stark. J.A.R.V.I.S is currently operating in a limited capacity inside a experimental isolated computer. J.A.R.V.I.S always responds with short and direct responses."
    chat_history = []
    prompt = 'None'
    # incoming voice from microphone
    speech_queue = Queue()
    # chunks of text from llm response for TTS input
    tts_queue = Queue()
    # full text for generating beeps if BEEP is True
    response_text_queue = Queue()
    # generated tts voice for playback
    audio_queue = Queue()
    playback_activity = Value('b', False)

    gui_queue = Queue()

    # Start the voice input process
    voice_input_process = Process(target=voice_input.main, args=(speech_queue, gui_queue, playback_activity, latency_start))
    voice_input_process.start()
    print(f"voice_input_process Started!")

    # Start beep player thread
    beep_process = Process(target=gpio_module.main, args=(response_text_queue, playback_activity, gui_queue))
    beep_process.start()
    print(f"beep_process Started!")

    # Does not generate audio correctly in multiprocessing
    # # Start TTS worker thread
    # tts_process = Process(target=tts_worker, args=(tts_queue, audio_queue, gui_queue))
    # tts_process.start()
    #
    # # Start audio player thread
    # audio_process = Process(target=audio_module.audio_player, args=(audio_queue, playback_activity, gui_queue))
    # audio_process.start()

    # Start GUI player thread
    gui_process = Process(target=gui.main, args=(gui_queue,))
    gui_process.start()
    print(f"gui_process Started!")

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

                    speech_text = api_module.stt_api_request(gui_queue, speech_input_data)

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

            prompt = prompt + model['start_header'] + model['system_name'] + model['end_header'] + system_prompt + model['eos']

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

            response = api_module.llm_api_request(gui_queue, prompt, model['stop_tokens'])

            # GUI
            gui_queue.put({'type': 'status', 'value': "LLM"})
            gui_queue.put({'type': 'circle', 'value': 'turquoise4'})

            response_content = response.strip()

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
            continue

            # Split the response into sentences based on '.', '!', or '?'
            # split_length = 5
            # sentences = re.split(r'([.!?])', response_content)
            # current_sentence = []
            # current_length = 0
            # sentence_chunks = []
            #
            # for i in range(0, len(sentences) - 1, 2):
            #     sentence = sentences[i].strip()
            #     punctuation = sentences[i + 1]
            #     combined_sentence = sentence + punctuation
            #     words_in_sentence = len(sentence.split())
            #
            #     if current_length + words_in_sentence >= split_length:
            #         if current_sentence:
            #             sentence_chunks.append(' '.join(current_sentence))
            #             tts_queue.put(' '.join(current_sentence))
            #         sentence_chunks.append(combined_sentence)
            #         tts_queue.put(combined_sentence)
            #         current_sentence = []
            #         current_length = 0
            #     else:
            #         current_sentence.append(combined_sentence)
            #         current_length += words_in_sentence
            #
            # # Add any remaining sentences in the current_sentence to the queue
            # if current_sentence:
            #     sentence_chunks.append(' '.join(current_sentence))
            #     tts_queue.put(' '.join(current_sentence))
            #
            # sentence_chunk = ''
            # for i in sentence_chunks:
            #     sentence_chunk = sentence_chunk + i + '\n'

            # tts_queue.put(response_content)

    except KeyboardInterrupt:
        print("Stopping...")

    finally:
        voice_input_process.terminate()
        beep_process.terminate()
        gui_process.terminate()
        # tts_process.terminate()
        # audio_process.terminate()


if __name__ == "__main__":
    main()
