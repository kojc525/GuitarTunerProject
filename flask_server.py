from flask import Flask, jsonify, render_template, request, redirect, url_for
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
# Flask web application instance
app = Flask(__name__)


#Home route: Renders the main page of the web application, displaying the list of guitar tunings.
@app.route('/')
def home():
    return render_template('tunings.html', tunings=tunings)


# Add Tuning route: Renders the page where users can add a new tuning.
@app.route('/add_tuning')
def add_tuning():
    return render_template('addTuning.html')


# Save Tuning route: Handles the POST request to save a new tuning.
# - Extracts tuning data from the form.
# - Adds the new tuning to the global 'tunings' list.
# - Saves the updated tunings list to the CSV file.
# - Redirects the user back to the home page.
@app.route('/save_tuning', methods=['POST'])
def save_tuning():
    tuning_name = request.form['tuningName']
    notes = [{request.form[f'note{i}']: float(request.form[f'frequencyValue{i}'])} for i in range(1, 7)]
    tunings.append({tuning_name: notes})

    export_tunings_to_csv()

    return redirect(url_for('home'))


# API Tunings route: Provides a JSON representation of the current guitar tunings.
# This can be used for API access to the tuning data.
@app.route('/api/tunings', methods=['GET'])
def get_tunings():
    return jsonify(tunings)


# Shutdown route: Allows for a clean shutdown of the Flask application.
# - Saves the current state of tunings to the CSV file before shutting down.
@app.route('/shutdown', methods=['POST'])
def shutdown():
    export_tunings_to_csv()

    # Flask-specific shutdown procedure
    func = request.environ.get('werkzeug.server.shutdown')
    if func:
        func()
    return 'Server shutting down...'


# Delete Tuning route: Handles the request to delete a specific guitar tuning.
# - This route receives the name of the tuning to be deleted as a URL parameter.
# - It then updates the global 'tunings' list by removing the specified tuning.
# - After removal, it saves the updated list of tunings to the CSV file.
# - Finally, it redirects the user back to the home page where the updated list is displayed.
@app.route('/delete_tuning/<tuning_name>')
def delete_tuning(tuning_name):
    global tunings
    # Update the tunings list by filtering out the tuning that matches the given name.
    tunings = [tuning for tuning in tunings if list(tuning.keys())[0] != tuning_name]

    # Save the updated list of tunings to the CSV file.
    export_tunings_to_csv()

    # Redirect the user back to the home page.
    return redirect(url_for('home'))

# -------------------------------------------------------------------


if __name__ == '__main__':
    # Initialization when the script is run.
    # Load tunings from the CSV file or create a new file with default tunings.
    load_tunings_from_csv()

    # Start the Flask application server.
    app.run(debug=True)