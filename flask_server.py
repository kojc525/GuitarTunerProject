from flask import Flask, jsonify, render_template

app = Flask(__name__)

# Dictionary containing different guitar tunings with note names and their corresponding frequencies in Hz.
tunings = {
    "Standard":          {"E2": 82.41, "A2": 110.00, "D3": 146.83, "G3": 196.00, "B3": 246.94, "E4": 329.63},
    "Drop D":            {"D2": 73.42, "A2": 110.00, "D3": 146.83, "G3": 196.00, "B3": 246.94, "E4": 329.63},
    "E Flat Tuning":     {"Eb2": 77.78, "Ab2": 103.83, "Db3": 138.59, "Gb3": 184.99, "Bb3": 233.08, "Eb4": 311.13},
    "D Standard Tuning": {"D2": 73.42, "G2": 97.99, "C3": 130.81, "F3": 174.61, "A3": 220.00, "D4": 293.66},
    "Open G Tuning":     {"D2": 73.42, "G2": 97.99, "D3": 146.83, "G3": 196.00, "B3": 246.94, "D4": 293.66},
    "Slash Tuning":      {"Eb2": 77.78, "Ab2": 103.83, "Db3": 138.59, "Gb3": 184.99, "Bb3": 233.08, "Eb4": 311.13}
}

@app.route('/')
def home():
    # Render an HTML page that lists the tunings
    return render_template('tunings.html', tunings=tunings)

@app.route('/api/tunings', methods=['GET'])
def get_tunings():
    # Return the tunings as JSON
    return jsonify(tunings)

if __name__ == '__main__':
    app.run(debug=True)