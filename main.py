import tkinter as tk
from tkinter import ttk
from tkinter import font
import tkinter.messagebox as messagebox
import sounddevice as sd
import numpy as np
import threading
import requests
from PIL import Image, ImageTk


# ***************************
# *    Global variables     *
# ***************************
# Global variables - app settings
# -------------------------------------------------------------------
# Dictionary containing different guitar tunings with note names and their corresponding frequencies in Hz.
# Local hardcoded tunings
local_tunings = [
    {"Standard":    [{"E2": 82.41}, {"A2": 110.00}, {"D3": 146.83}, {"G3": 196.00}, {"B3": 246.94}, {"E4": 329.63}]},
    {"Drop D":      [{"D2": 73.42}, {"A2": 110.00}, {"D3": 146.83}, {"G3": 196.00}, {"B3": 246.94}, {"E4": 329.63}]}
]

# Server URL link where the app gets tunings (API)
server_link = 'http://localhost:5000/api/tunings'

# Duration for each audio capture cycle in seconds.
# Lower = faster app but less precise
# Higher = slower app but more precise
detection_speed = 0.4  # sec

# Frequency indicator
turn_indicator_green = 2  # Hz - Turns indicator green when input_frequency is within this much of target_frequency
turn_indicator_red = 50   # Hz - Turns indicator red when input_frequency is this far from target_frequency


# Other global variables - DO NOT MODIFY
# -------------------------------------------------------------------
# Server tunings - are loded in with the API
server_tunings = {}

# Tunings currently used by the app
tunings = {}

# List of string buttons
string_buttons = []

# List of available input devices for audio capture.
input_devices = ["Device1"]

# Dictionary to store the currently targeted frequency information.
target_frequency = {'note': 'Note', 'frequency': 0}

# Variable to store the detected input frequency (initialized to 0 Hz for testing purposes).
input_frequency = 0

# Global variable for the thread used in detection; initialized to None.
detection_thread = None

# Global variable to control the state of the audio detection process.
# It is used as a flag to start or stop the continuous detection in a separate thread.
# When set to True, the detection process runs; when set to False, the detection stops.
continue_detection = False

# Global Variable where the app gets the tunings
tunings_list_source = None  # Default to 'Local'


# ***************************
# *        Functions        *
# ***************************
# Server Functions
# -------------------------------------------------------------------
# Function to Load Tunings from Server
def load_server_tunings():
    global server_tunings, tunings, server_link
    try:
        # Make an HTTP GET request to the specified URL which is the API endpoint for guitar tunings.
        response = requests.get(server_link)
        if response.status_code == 200:
            print("-" * 22 + "\nConnected to server!\n" + "-" * 22)
            # Parse the JSON response from the server into a Python dictionary.
            server_tunings = response.json()
            # Use server tunings in the app
            tunings = server_tunings

            # Print imported tunings to the console.
            print("Tunings imported:")
            for tuning_dict in tunings:
                for tuning_name, notes_list in tuning_dict.items():
                    print(f"{tuning_name:22}:", notes_list)
        else:
            print("ERROR! - Server response status code:", response.status_code)
            messagebox.showerror("Connection Error", f"Server response status code:\n{response.status_code}")
            # Set radio button back to Local
            tunings_list_source.set("Local")
            update_tunings()
    except requests.exceptions.RequestException as e:
        print("\nERROR! - Failed to connect to server\nDetails:")
        print(e)
        messagebox.showerror("Connection Error",
                             f"Failed to connect to the server. Tuning will be loaded from 'Local'.\n\nDetails:\n{e}")
        # Set radio button back to Local
        tunings_list_source.set("Local")
        update_tunings()



# GUI Functions
# -------------------------------------------------------------------
# Updates the text on string buttons based on the selected tuning.
def update_string_buttons(tuning_name):
    global string_buttons
    # Find the dictionary for the given tuning name.
    tuning_dict = next((item for item in tunings if tuning_name in item), None)
    if tuning_dict:
        # Clear the previous buttons
        for btn in string_buttons:
            btn.grid_forget()
        string_buttons.clear()

        # Reset the target note display
        global target_frequency
        target_frequency = {'note': 'Note', 'frequency': 0.00}
        target_note_label.config(text=f"{target_frequency['note']} - {target_frequency['frequency']:.2f} Hz")

        notes_list = tuning_dict[tuning_name]

        # Create new buttons for the selected tuning
        for i, note_dict in enumerate(notes_list):
            for note, freq in note_dict.items():
                button_text = f"{note} - {freq:.2f} Hz"
                # Create a new button with the note and frequency
                btn = tk.Button(root, text=button_text, padx=5, pady=5,
                                command=lambda note=note, freq=freq: string_button_click(note, freq))
                btn.grid(row=4 + i, column=1, sticky="ew", padx=[0,5])
                string_buttons.append(btn)


# Handles the event when a string button is clicked.
def string_button_click(note, freq):
    # Updating the target frequency based on the selected string.
    global target_frequency
    target_frequency['note'] = note
    target_frequency['frequency'] = freq

    # Resetting the background color of all buttons and setting the clicked button to green.
    # We must find the button associated with the note
    for button in string_buttons:
        if button['text'].startswith(note):  # Check if the button's text starts with the note name
            button.config(bg="#05e1fa")
        else:
            button.config(bg="SystemButtonFace")

    # Updating the target note label with the note name and frequency, formatted to two decimal places.
    target_note_label.config(text=f"{note} - {freq:.2f} Hz")


# Function to Update Tunings Based on Radio Button Selection
def update_tunings():
    global tunings
    if tunings_list_source.get() == "Local":
        tunings = local_tunings
    else:
        load_server_tunings()
    update_combobox()


# Function to Update Combobox with New Tunings
def update_combobox():
    tuning_names = [list(tuning.keys())[0] for tuning in tunings]
    tuning_combobox.config(values=tuning_names)
    if tuning_names:
        tuning_combobox.current(0)
        update_string_buttons(tuning_combobox.get())


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
        global continue_detection
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
                # Compare input frequency with target frequency and update the indicator
                frequency_difference = abs(target_frequency['frequency'] - dominant_frequency)
                # Check if the dominant frequency is within [turn_indicator_green] Hz of the target frequency
                if frequency_difference < turn_indicator_green:
                    tuning_indicator_label.config(text="[  >> | << ]", fg='green')
                elif frequency_difference > turn_indicator_red:
                    # If the difference is greater than [turn_indicator_red] Hz, display the indicator in red
                    if target_frequency['frequency'] > dominant_frequency:
                        tuning_indicator_label.config(text="[ >> |     ]", fg='red')
                    else:
                        tuning_indicator_label.config(text="[     | << ]", fg='red')
                else:
                    # For differences between 3 Hz and 50 Hz, display the indicator in black
                    if target_frequency['frequency'] > dominant_frequency:
                        tuning_indicator_label.config(text="[  > |     ]", fg='white')
                    else:
                        tuning_indicator_label.config(text="[     | <  ]", fg='white')
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

    tuning_indicator_label.config(text="[     |     ]", fg='black')  # Stop showing tuning label


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


# ***************************
# *          MAIN           *
# ***************************
# -------------------------------------------------------------------
# Initialize and get the list of input devices.
get_input_devices()


# GUI Section
# -------------------------------------------------------------------
# Create the main application window
root = tk.Tk()
root.title("Guitar Tuner")  # Set the title of the window
root.geometry('540x605')  # Set the fixed size of the window
root.configure(bg='black')  # Set the background color of the root window

# Disable resizing of the window
root.resizable(False, False)

# Load the background image
bg_image = Image.open('static/bg2.jpg')

# Resize the image to 30% of its original size
width, height = bg_image.size
new_width = int(width * 0.15)
new_height = int(height * 0.15)
bg_image = bg_image.resize((new_width, new_height), Image.Resampling.LANCZOS)

bg_photo = ImageTk.PhotoImage(bg_image)

# Create a frame for the image and place it in the fourth column
image_frame = tk.Frame(root, highlightbackground='black', highlightthickness=0)
image_frame.grid(row=0, column=3, rowspan=15, sticky='ns')

# Place the image inside the frame
bg_label = tk.Label(image_frame, image=bg_photo, borderwidth=0)
bg_label.pack(expand=True, fill='both', padx=0, pady=0)

root.protocol("WM_DELETE_WINDOW", on_closing)  # Bind the closing protocol to the on_closing function

# Configure the grid layout of the root window
root.grid_columnconfigure(1, weight=1)
root.grid_columnconfigure(2, weight=1)

# Create a custom font for the label
custom_font = font.Font(family="Arial", size=10, weight="bold")

# ----- TARGET NOTE TO HIT -----
# Create and place label for displaying the targeted note
tk.Label(root, text="Target note:", bg='black', fg='#05e1fa', font=custom_font).grid(row=10, column=0, sticky="w", padx=10)
target_note_label = tk.Label(root, text=f"{target_frequency['note']} - {target_frequency['frequency']:.2f} Hz",
                             bg='black', fg='white', font=custom_font)
target_note_label.grid(row=10, column=1, sticky="w")


# ----- TUNING SELECTION -----
# Initialize tunings_list_source variable
tunings_list_source = tk.StringVar(value="Local")  # Default to 'Local'
# Radio Buttons for Tuning Source
tk.Label(root, text="Get tuning from:", bg='black', fg='#05e1fa', font=custom_font).grid(row=0, column=0,
                                                                                         sticky="w", padx=10)
tk.Radiobutton(root, text="Local", variable=tunings_list_source, value="Local", command=update_tunings, bg='black',
               fg='white', font=custom_font, selectcolor='black').grid(row=0, column=1, sticky="w")
tk.Radiobutton(root, text="Server", variable=tunings_list_source, value="Server", command=update_tunings, bg='black',
               fg='white', font=custom_font, selectcolor='black').grid(row=0, column=2, sticky="w")

# Tuning Selection Combobox
# Set Local tunings as default
tunings = local_tunings
tk.Label(root, text="Tuning:", bg='black', fg='#05e1fa', font=custom_font).grid(row=1, column=0, sticky="w", padx=10)
tuning_var = tk.StringVar(root)
tuning_combobox = ttk.Combobox(root, textvariable=tuning_var, state="readonly")
tuning_combobox.grid(row=1, column=1, columnspan=2, sticky="ew", padx=[0, 15], pady=5)
tuning_combobox.bind('<<ComboboxSelected>>', lambda event: update_string_buttons(tuning_var.get()))
update_combobox()


# ----- INPUT SELECTION -----
# Create and place the input device selection label and combobox
tk.Label(root, text="Input device:", bg='black', fg='#05e1fa', font=custom_font).grid(row=2, column=0, sticky="w", padx=10)
input_device_var = tk.StringVar(root)
input_device_combobox = ttk.Combobox(root, textvariable=input_device_var, values=input_devices, state="readonly")
input_device_combobox.grid(row=2, column=1, columnspan=2, sticky="ew", padx=[0,15], pady=5)
input_device_combobox.current(0)  # Initialize with the first input device option selected


# ----- GUITAR STRING BUTTONS -----
# Create and place buttons for each string based on the selected tuning
tk.Label(root, text="Choose string:", bg='black', fg='#05e1fa', font=custom_font).grid(row=3, column=0, sticky="w", padx=10)
string_buttons = []
# Since tunings is a list of dictionaries, we extract the first tuning's notes by default.
# You may want to do this after a tuning is selected from the combobox instead.
selected_tuning_dict = tunings[tuning_combobox.current()]  # get the current selected tuning
selected_tuning_name = tuning_var.get()  # get the name of the tuning
notes_list = selected_tuning_dict[selected_tuning_name]  # get the list of notes for this tuning
# Create buttons for each note in the selected tuning
for i, note_dict in enumerate(notes_list):
    for note, freq in note_dict.items():
        button_text = f"{note} - {freq:.2f} Hz"
        btn = tk.Button(root, text=button_text, padx=5, pady=5,
                        command=lambda note=note, freq=freq: string_button_click(note, freq))
        btn.grid(row=4 + i, column=1, sticky="ew", padx=[0, 5])
        string_buttons.append(btn)


# ----- DOMINANT INPUT FREQUENCY -----
# Create and place label for displaying the detected input sound frequency
tk.Label(root, text="Input sound:", bg='black', fg='#05e1fa', font=custom_font).grid(row=11, column=0, sticky="w", padx=10)
input_sound_label = tk.Label(root, text=f"{input_frequency} Hz", bg='black', fg='white', font=custom_font)
input_sound_label.grid(row=11, column=1, sticky="w")


# ----- TUNING INDICATOR -----
# Tuning Indicator Label
tuning_indicator_label = tk.Label(root, text="[     |     ]", font=("Courier", 12, "bold"), bg='black', fg='white')
tuning_indicator_label.grid(row=12, column=1, sticky="ew")


# ----- START / STOP TUNING -----
# Create and place labels and buttons for starting and stopping frequency detection
detect_freq_label = tk.Label(root, text=f"Start tuning:", padx=10, bg='black', fg='#05e1fa', font=custom_font)
detect_freq_label.grid(row=13, column=0, sticky="w")
detect_freq_button = tk.Button(root, text="Start", command=start_frequency_detection, width=40)  # Button to start detection
detect_freq_button.grid(row=13, column=1, padx=10, pady=5, sticky="ew")
stop_freq_button = tk.Button(root, text="Stop", command=stop_frequency_detection, width=40)  # Button to stop detection
stop_freq_button.grid(row=13, column=2, padx=10, pady=5, sticky="ew")


# ----- SIGNITURE -----
# Create and place a signature label
signiture_label = tk.Label(root, text=f"by Kojc", bg='black', fg='#05e1fa', font=custom_font)
signiture_label.grid(row=14, column=2, sticky="e", padx=[0,15])


# Start the Tkinter main event loop
root.mainloop()
