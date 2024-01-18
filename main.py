import tkinter as tk
from tkinter import ttk
import sounddevice as sd
import numpy as np
import threading


# Global variables
# -------------------------------------------------------------------
# Dictionary containing different guitar tunings with note names and their corresponding frequencies in Hz.
tunings = {
    "Standard": {"E2": 82.41, "A2": 110.00, "D3": 146.83, "G3": 196.00, "B3": 246.94, "E4": 329.63},
    "Drop D": {"D2": 73.42, "A2": 110.00, "D3": 146.83, "G3": 196.00, "B3": 246.94, "E4": 329.63}
}
# List of available input devices for audio capture.
input_devices = ["Device1"]

# Dictionary to store the currently targeted frequency information.
target_frequency = {'note': 'Note', 'frequency': 0}

# Variable to store the detected input frequency (initialized to 0 Hz for testing purposes).
input_frequency = 0

# Global variable for the thread used in detection; initialized to None.
detection_thread = None

# Duration for each audio capture cycle in seconds.
detection_speed = 0.5





# GUI Functions
# -------------------------------------------------------------------
# Updates the text on string buttons based on the selected tuning.
def update_string_buttons(tuning):
    # Iterating over each note in the selected tuning.
    notes = tunings[tuning]
    for i, (note, freq) in enumerate(notes.items()):
        # Configuring each string button with the note name and setting up its command.
        string_buttons[i].config(text=note, command=lambda i=i, note=note, freq=freq: string_button_click(i, note, freq))


# Handles the event when a string button is clicked.
def string_button_click(index, note, freq):
    # Updating the target frequency based on the selected string.
    global target_frequency
    target_frequency['note'] = note
    target_frequency['frequency'] = freq

    # Resetting the background color of all buttons and setting the clicked button to green.
    for button in string_buttons:
        button.config(bg="SystemButtonFace")
    string_buttons[index].config(bg="green")

    # Updating the target note label with the note name and frequency, formatted to two decimal places.
    target_note_label.config(text=f"{note} - {freq:.2f} Hz")


# Functions for handling input devices
# -------------------------------------------------------------------
# Retrieves and lists all available input devices with audio input capabilities.
def get_input_devices():
    global input_devices
    devices = sd.query_devices()
    # Creating a list of input device names along with their index for unique identification.
    input_devices = [f"{device['name']} [{index}]" for index, device in enumerate(devices) if
                     device['max_input_channels'] > 0]


# Functions for audio signal processing
# -------------------------------------------------------------------
# Records audio for a specified duration and samplerate.
def record_audio(duration=1.0, samplerate=44100):
    # Set the samplerate and channel configuration for recording.
    sd.default.samplerate = samplerate
    sd.default.channels = 1
    # Record audio for the given duration and return the recording.
    recording = sd.rec(int(duration * samplerate))
    sd.wait()  # Wait until the recording is finished
    return recording


# Calculates and returns the dominant frequency from an audio recording.
def calculate_dominant_frequency(recording, samplerate=44100):
    # Perform a Fast Fourier Transform (FFT) on the recording.
    fft_spectrum = np.fft.rfft(recording.flatten())
    # Calculate the frequencies corresponding to the FFT results.
    frequencies = np.fft.rfftfreq(len(recording), 1.0 / samplerate)
    # Identify the frequency with the highest amplitude, which is the dominant frequency.
    dominant_frequency = frequencies[np.argmax(np.abs(fft_spectrum))]
    return dominant_frequency


# Functions for controlling frequency detection
# -------------------------------------------------------------------
# Starts the frequency detection process in a separate thread.
def start_frequency_detection():
    def detect():
        # Continuously detect frequency while the flag is true.
        while continue_detection:
            # Retrieve and set the selected input device.
            selected_device_str = input_device_var.get()
            device_index = int(selected_device_str.split('[')[-1].rstrip(']'))
            sd.default.device = device_index
            # Record audio and calculate its dominant frequency.
            recording = record_audio(duration=detection_speed)
            dominant_frequency = calculate_dominant_frequency(recording)

            # Update the GUI with the detected frequency, unless detection has been stopped.
            if continue_detection:
                input_sound_label.config(text=f"{dominant_frequency:.2f} Hz")
            else:
                break  # Exit the loop if detection is stopped.

    global continue_detection
    # Change button colors to reflect the current state of detection.
    detect_freq_button.config(bg='green', activebackground='green')  # Start button green
    stop_freq_button.config(bg='SystemButtonFace', activebackground='SystemButtonFace')  # Stop button default
    continue_detection = True
    # Start the detection thread.
    detection_thread = threading.Thread(target=detect)
    detection_thread.start()


# Stops the ongoing frequency detection process.
def stop_frequency_detection():
    global continue_detection
    # Set the flag too False to stop the detection.
    continue_detection = False
    # Reset the displayed frequency and change button colors.
    input_sound_label.config(text="0 Hz")
    detect_freq_button.config(bg='SystemButtonFace', activebackground='SystemButtonFace')  # Start button default
    stop_freq_button.config(bg='red', activebackground='red')  # Stop button red


# Function to handle the window closing event
# -------------------------------------------------------------------
# Called when the application window is closed.
def on_closing():
    global continue_detection, detection_thread
    # If detection is ongoing, stop it and wait for the thread to finish.
    if continue_detection:
        continue_detection = False
        if detection_thread is not None:
            detection_thread.join()
    # Close the application window.
    root.destroy()





# MAIN execution
# -------------------------------------------------------------------
# Initialize and get the list of input devices.
get_input_devices()


# GUI Section
# -------------------------------------------------------------------
# Create the main application window
root = tk.Tk()
root.title("Guitar Tuner")  # Set the title of the window
root.geometry('300x400')  # Set the fixed size of the window
root.protocol("WM_DELETE_WINDOW", on_closing)  # Bind the closing protocol to the on_closing function


# Configure the grid layout of the root window
root.grid_columnconfigure(1, weight=1)
root.grid_columnconfigure(2, weight=1)


# Create and place the tuning selection label and combobox
tk.Label(root, text="Tuning:").grid(row=0, column=0, sticky="w", padx=10)
tuning_var = tk.StringVar(root)
tuning_combobox = ttk.Combobox(root, textvariable=tuning_var, values=list(tunings.keys()), state="readonly")
tuning_combobox.grid(row=0, column=1, columnspan=2, sticky="ew", padx=[0,15], pady=5)
tuning_combobox.current(0)  # Initialize with the first tuning option selected
tuning_combobox.bind('<<ComboboxSelected>>', lambda event: update_string_buttons(tuning_var.get()))  # Update string buttons when a tuning is selected


# Create and place the input device selection label and combobox
tk.Label(root, text="Input device:").grid(row=1, column=0, sticky="w", padx=10)
input_device_var = tk.StringVar(root)
input_device_combobox = ttk.Combobox(root, textvariable=input_device_var, values=input_devices, state="readonly")
input_device_combobox.grid(row=1, column=1, columnspan=2, sticky="ew", padx=[0,15], pady=5)
input_device_combobox.current(0)  # Initialize with the first input device option selected


# Create and place buttons for each string based on the selected tuning
tk.Label(root, text="Choose string:").grid(row=2, column=0, sticky="w", padx=10)
string_buttons = []
for i, (note, freq) in enumerate(tunings[tuning_var.get()].items()):
    btn = tk.Button(root, text=note, padx=5, pady=5, command=lambda i=i, note=note, freq=freq: string_button_click(i, note, freq))
    btn.grid(row=3 + i, column=1, sticky="ew", padx=[0,5])
    string_buttons.append(btn)  # Add button to the list for later reference


# Create and place label for displaying the targeted note
tk.Label(root, text="Target note:").grid(row=9, column=0, sticky="w", padx=10)
target_note_label = tk.Label(root, text=f"{target_frequency['note']} - {target_frequency['frequency']:.2f} Hz")
target_note_label.grid(row=9, column=1, sticky="w")


# Create and place label for displaying the detected input sound frequency
tk.Label(root, text="Input sound:").grid(row=10, column=0, sticky="w", padx=10)
input_sound_label = tk.Label(root, text=f"{input_frequency} Hz")
input_sound_label.grid(row=10, column=1, sticky="w")


# Create and place labels and buttons for starting and stopping frequency detection
detect_freq_label = tk.Label(root, text=f"Start tuning:", padx=10)
detect_freq_label.grid(row=11, column=0, sticky="w")
detect_freq_button = tk.Button(root, text="Start", command=start_frequency_detection)  # Button to start detection
detect_freq_button.grid(row=11, column=1, padx=10, pady=5, sticky="ew")
stop_freq_button = tk.Button(root, text="Stop", command=stop_frequency_detection)  # Button to stop detection
stop_freq_button.grid(row=11, column=2, padx=10, pady=5, sticky="ew")


# Create and place a signature label
signiture_label = tk.Label(root, text=f"by Kojc")
signiture_label.grid(row=12, column=2, sticky="e", padx=[0,15])


# Start the Tkinter main event loop
root.mainloop()
