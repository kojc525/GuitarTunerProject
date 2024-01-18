import tkinter as tk
from tkinter import ttk
import sounddevice as sd
import numpy as np


# Global variables
# -------------------------------------------------------------------
tunings = {
    "Standard": {"E2": 82.41, "A2": 110.00, "D3": 146.83, "G3": 196.00, "B3": 246.94, "E4": 329.63},
    "Drop D": {"D2": 73.42, "A2": 110.00, "D3": 146.83, "G3": 196.00, "B3": 246.94, "E4": 329.63}
}
input_devices = ["Device1"]
target_frequency = {'note': '', 'frequency': 0}
input_frequency = 100  # Hz for testing


# Functions GUI
# -------------------------------------------------------------------
# Function to update string buttons based on selected tuning
def update_string_buttons(tuning):
    notes = tunings[tuning]
    for i, (note, freq) in enumerate(notes.items()):
        string_buttons[i].config(text=note, command=lambda i=i, note=note, freq=freq: string_button_click(i, note, freq))


# Function to handle string button click
def string_button_click(index, note, freq):
    global target_frequency
    target_frequency['note'] = note
    target_frequency['frequency'] = freq
    for button in string_buttons:
        button.config(bg="SystemButtonFace")
    string_buttons[index].config(bg="green")
    # Use ':.2f' to format the frequency to two decimal places
    target_note_label.config(text=f"{note} - {freq:.2f} Hz")


# Functions INPUT DEVICES
# -------------------------------------------------------------------
def get_input_devices():
    global input_devices
    devices = sd.query_devices()
    input_devices = [f"{device['name']} [{index}]" for index, device in enumerate(devices) if device['max_input_channels'] > 0]


# Button to start frequency detection
def start_frequency_detection():
    selected_device_str = input_device_var.get()
    # Extract the device index from the string
    device_index = int(selected_device_str.split('[')[-1].rstrip(']'))
    sd.default.device = device_index
    recording = record_audio()
    dominant_frequency = calculate_dominant_frequency(recording)
    input_sound_label.config(text=f"{dominant_frequency:.2f} Hz")


# Functions SIGNAL PROCESSING
# -------------------------------------------------------------------
# Record audio for a given duration and samplerate
def record_audio(duration=1.0, samplerate=44100):
    sd.default.samplerate = samplerate
    sd.default.channels = 1
    recording = sd.rec(int(duration * samplerate))
    sd.wait()
    return recording


# Calculate the dominant frequency of an audio sample.
def calculate_dominant_frequency(recording, samplerate=44100):
    fft_spectrum = np.fft.rfft(recording.flatten())
    frequencies = np.fft.rfftfreq(len(recording), 1.0/samplerate)
    dominant_frequency = frequencies[np.argmax(np.abs(fft_spectrum))]
    return dominant_frequency


# MAIN
# -------------------------------------------------------------------
get_input_devices()


# GUI
# -------------------------------------------------------------------
# Create main window
root = tk.Tk()
root.title("Guitar Tuner")
# Set the window to a fixed size
root.geometry('300x400')


# Configure the grid
root.grid_columnconfigure(1, weight=1)
root.grid_columnconfigure(2, weight=1)


# Tuning selection
tk.Label(root, text="Tuning:").grid(row=0, column=0, sticky="w")
tuning_var = tk.StringVar(root)
tuning_combobox = ttk.Combobox(root, textvariable=tuning_var, values=list(tunings.keys()), state="readonly")
tuning_combobox.grid(row=0, column=1, columnspan=2, sticky="ew", padx=[0,15], pady=5)
tuning_combobox.current(0)  # Set the default selection to the first tuning in the list
tuning_combobox.bind('<<ComboboxSelected>>', lambda event: update_string_buttons(tuning_var.get()))  # Update buttons on selection


# Input device selection
tk.Label(root, text="Input device:").grid(row=1, column=0, sticky="w")
input_device_var = tk.StringVar(root)
input_device_combobox = ttk.Combobox(root, textvariable=input_device_var, values=input_devices, state="readonly")
input_device_combobox.grid(row=1, column=1, columnspan=2, sticky="ew", padx=[0,15], pady=5)
input_device_combobox.current(0)  # Set the default selection to the first input device in the list


# String buttons
tk.Label(root, text="Choose string:").grid(row=2, column=0, sticky="w")
string_buttons = []
for i, (note, freq) in enumerate(tunings[tuning_var.get()].items()):
    btn = tk.Button(root, text=note, padx=5, pady=5,
                    command=lambda i=i, note=note, freq=freq: string_button_click(i, note, freq))
    btn.grid(row=3 + i, column=1, sticky="ew", padx=[0,5])
    string_buttons.append(btn)


# Target note
tk.Label(root, text="Target note:").grid(row=9, column=0, sticky="w")
target_note_label = tk.Label(root, text=f"{target_frequency['note']} - {target_frequency['frequency']:.2f} Hz")
target_note_label.grid(row=9, column=1, sticky="w")


# Input sound
tk.Label(root, text="Input sound:").grid(row=10, column=0, sticky="w")
input_sound_label = tk.Label(root, text=f"{input_frequency} Hz")
input_sound_label.grid(row=10, column=1, sticky="w")


# Start detecting
detect_freq_button = tk.Button(root, text="Start detecting", command=start_frequency_detection)
detect_freq_button.grid(row=11, column=0, columnspan=3, pady=[10,10])


# Signiture
signiture_label = tk.Label(root, text=f"by Kojc")
signiture_label.grid(row=12, column=2, sticky="e", padx=[0,15])


# Start the main loop
root.mainloop()
