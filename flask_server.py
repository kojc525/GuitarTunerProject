from flask import Flask, jsonify, render_template
import csv
import os


# ***************************
# *    Global variables     *
# ***************************
# -------------------------------------------------------------------
# Tunings that load into 'tunings.csv' when it is first created
# Each item in the list is a dictionary representing a tuning type and its corresponding notes with frequencies.
first_load_tunings = [
    {"Standard":            [{"E2": 82.41}, {"A2": 110.00}, {"D3": 146.83}, {"G3": 196.00}, {"B3": 246.94}, {"E4": 329.63}]},
    {"Drop D":              [{"D2": 73.42}, {"A2": 110.00}, {"D3": 146.83}, {"G3": 196.00}, {"B3": 246.94}, {"E4": 329.63}]},
    {"E Flat Tuning":       [{"Eb2": 77.78}, {"Ab2": 103.83}, {"Db3": 138.59}, {"Gb3": 184.99}, {"Bb3": 233.08}, {"Eb4": 311.13}]},
    {"D Standard Tuning":   [{"D2": 73.42}, {"G2": 97.99}, {"C3": 130.81}, {"F3": 174.61}, {"A3": 220.00}, {"D4": 293.66}]},
    {"Open G Tuning":       [{"D2": 73.42}, {"G2": 97.99}, {"D3": 146.83}, {"G3": 196.00}, {"B3": 246.94}, {"D4": 293.66}]},
    {"Slash Tuning":        [{"Eb2": 77.78}, {"Ab2": 103.83}, {"Db3": 138.59}, {"Gb3": 184.99}, {"Bb3": 233.08}, {"Eb4": 311.13}]}
]

# A list to store the current tunings loaded into the server.
tunings = []

# The file path where tunings are stored.
tunings_file = 'tunings.csv'


# ***************************
# *        Functions        *
# ***************************
# Functions for handling tuning storage and retrieval.
# -------------------------------------------------------------------
# Function to load tunings from a CSV file
# This function checks if a CSV file exists. If it doesn't,
# it creates the file using 'first_load_tunings'.
# If the file exists, it loads the tunings from the file into the 'tunings' list.
def load_tunings_from_csv():
    # Loads tunings from a CSV file into the global 'tunings' list.
    global tunings_file, first_load_tunings, tunings
    file_path = tunings_file

    # Check if the CSV file exists.
    if not os.path.exists(file_path):
        # If the file does not exist, set 'tunings' to 'first_load_tunings' and create the file.
        tunings = first_load_tunings
        export_tunings_to_csv()
    else:
        # If the file exists, read the tunings from the file.
        with open(file_path, 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                # Each row represents a tuning, with the first element being the tuning name and subsequent elements being notes and frequencies.
                tuning_name = row[0]
                notes = [{row[i]: float(row[i + 1])} for i in range(1, len(row), 2)]
                tunings.append({tuning_name: notes})


# Function to export/save tunings to a CSV file
# This function writes the current tunings in the 'tunings' list to a CSV file.
def export_tunings_to_csv():
    # Exports the current tunings to a CSV file.
    global tunings, tunings_file
    with open(tunings_file, 'w', newline='') as file:
        writer = csv.writer(file)
        for tuning in tunings:
            for tuning_name, notes in tuning.items():
                # Construct a row for each tuning, with the tuning name followed by note-frequency pairs.
                row = [tuning_name]
                for note in notes:
                    for note_name, frequency in note.items():
                        row.extend([note_name, frequency])
                writer.writerow(row)


# ***************************
# *          MAIN           *
# ***************************
# Flask web application setup and routes.
# -------------------------------------------------------------------
app = Flask(__name__)

@app.route('/')
def home():
    # Route to render an HTML page that lists the current tunings.
    return render_template('tunings.html', tunings=tunings)

@app.route('/add_tuning')
def add_tuning():
    return render_template('addTuning.html')

@app.route('/api/tunings', methods=['GET'])
def get_tunings():
    # API route to return the current tunings in JSON format.
    return jsonify(tunings)

@app.route('/shutdown', methods=['POST'])
def shutdown():
    # Route to shut down the server and export current tunings to CSV before closing.
    export_tunings_to_csv()

if __name__ == '__main__':
    # Load tunings from CSV or create new file with default tunings when the application starts.
    load_tunings_from_csv()
    # Start the Flask application.
    app.run(debug=True)