import tkinter as tk
from tkinter import ttk
from multiprocessing import Queue
import queue

gui_queue = Queue()

chat_history = 'Chat History\n" + "-"*50 + "\n" + "Sample chat history...'
response_text = 'Response Text\n" + "-"*50 + "\n" + "Sample response text...'
text_chunks = 'Text Chunks\n" + "-"*50 + "\n" + "Sample text chunks...'


# Function to update the circle indicator color
def update_circle(color):
    canvas.itemconfig(circle, fill=color)


# Function to update the status text
def update_status(new_status):
    status_label.config(text=new_status)


# Function to update the main text display
def update_main_text(new_text):
    main_text.config(state=tk.NORMAL)
    main_text.delete(1.0, tk.END)
    main_text.insert(tk.END, new_text)
    main_text.config(state=tk.DISABLED)


# Functions to update latency values
def update_tts_latency(latency):
    tts_latency_var.set(f"TTS Latency: {latency} ms")


def update_stt_latency(latency):
    stt_latency_var.set(f"STT Latency: {latency} ms")


def update_llm_latency(latency):
    llm_latency_var.set(f"LLM Latency: {latency} ms")


# Setting up the main window
window = tk.Tk()
window.title("Voice Assistant GUI")

# Canvas for the circle indicator
canvas = tk.Canvas(window, width=100, height=100)
canvas.pack(pady=10)
circle = canvas.create_oval(10, 10, 90, 90, fill="black")

# Status label under the circle
status_label = tk.Label(window, text="empty", font=("Helvetica", 14))
status_label.pack(pady=5)

# Large main text display field
main_text = tk.Text(window, wrap=tk.WORD, state=tk.DISABLED, width=60, height=20)
main_text.pack(padx=10, pady=10)

# Frame for buttons
button_frame = tk.Frame(window)
button_frame.pack(pady=10)

chat_history_button = ttk.Button(button_frame, text="Chat History", command=lambda: gui_queue.put({'type': 'chat_history', 'value': chat_history}))
chat_history_button.grid(row=0, column=0, padx=5)

response_text_button = ttk.Button(button_frame, text="Response Text", command=lambda: gui_queue.put({'type': 'response_text', 'value': response_text}))
response_text_button.grid(row=0, column=1, padx=5)

text_chunks_button = ttk.Button(button_frame, text="Text Chunks", command=lambda: gui_queue.put({'type': 'text_chunks', 'value': text_chunks}))
text_chunks_button.grid(row=0, column=2, padx=5)

# Latency display fields
tts_latency_var = tk.StringVar()
stt_latency_var = tk.StringVar()
llm_latency_var = tk.StringVar()

tts_latency_label = tk.Label(window, textvariable=tts_latency_var)
tts_latency_label.pack()

stt_latency_label = tk.Label(window, textvariable=stt_latency_var)
stt_latency_label.pack()

llm_latency_label = tk.Label(window, textvariable=llm_latency_var)
llm_latency_label.pack()

# Set initial latency values
update_tts_latency(0)
update_stt_latency(0)
update_llm_latency(0)


def main(queue):
    global gui_queue, chat_history, response_text, text_chunks
    gui_queue = queue
    # window.mainloop()

    while True:
        try:
            while not gui_queue.empty():
                update = gui_queue.get_nowait()
                if update['type'] == 'status':
                    update_status(update['value'])
                elif update['type'] == 'circle':
                    update_circle(update['value'])
                elif update['type'] == 'chat_history':
                    update_main_text(update['value'])
                    chat_history = update['value']
                elif update['type'] == 'response_text':
                    update_main_text(update['value'])
                    response_text = update['value']
                elif update['type'] == 'text_chunks':
                    update_main_text(update['value'])
                    text_chunks = update['value']
                elif update['type'] == 'tts_latency':
                    update_tts_latency(update['value'])
                elif update['type'] == 'stt_latency':
                    update_stt_latency(update['value'])
                elif update['type'] == 'llm_latency':
                    update_llm_latency(update['value'])
        except queue.Empty:
            pass
        window.update_idletasks()
        window.update()


if __name__ == "__main__":
    main(gui_queue=Queue())
