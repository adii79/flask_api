import os
import csv
import datetime
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Global API keys for read and write operations
READ_API_KEY = 'read-api-key'
WRITE_API_KEY = 'write-api-key'

# Firebase configuration
FIREBASE_URL = "https://your-firebase-database.firebaseio.com"  # Replace with your Firebase Realtime Database URL

# Predefined channels for data transfer
channels_data = {
    "channel1": [],
    "channel2": [],
    "channel3": []  # Add more channels as needed
}

# Helper function to save data for a channel
def save_to_channel(channel, sensor_name, sensor_value, timestamp):
    # Save to in-memory dictionary
    data_entry = {
        "sensor_name": sensor_name,
        "sensor_value": sensor_value,
        "timestamp": timestamp
    }
    channels_data[channel].append(data_entry)

    # Save to CSV file
    with open("data.csv", mode="a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([channel, sensor_name, sensor_value, timestamp])

# Endpoint to write data to the server (from hardware)
@app.route('/write/<channel>', methods=['POST'])
def write_data(channel):
    api_key = request.args.get('key')
    if api_key != WRITE_API_KEY:
        return jsonify({"message": "Invalid Write API key", "status": "error"}), 403

    if channel not in channels_data:
        return jsonify({"message": "Invalid channel", "status": "error"}), 404

    content = request.json
    if not content or 'sensor_name' not in content or 'sensor_value' not in content:
        return jsonify({"message": "Invalid data format", "status": "error"}), 400

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_to_channel(channel, content['sensor_name'], content['sensor_value'], timestamp)

    return jsonify({"message": "Data stored successfully!", "status": "success"}), 200

# Endpoint to read data from the server
@app.route('/read/<channel>', methods=['GET'])
def read_data(channel):
    api_key = request.args.get('key')
    if api_key != READ_API_KEY:
        return jsonify({"message": "Invalid Read API key", "status": "error"}), 403

    if channel not in channels_data:
        return jsonify({"message": "Invalid channel", "status": "error"}), 404

    return jsonify(channels_data[channel]), 200

# Endpoint to post data to Firebase
@app.route('/post_to_firebase', methods=['POST'])
def post_to_firebase():
    api_key = request.args.get('key')
    if api_key != WRITE_API_KEY:
        return jsonify({"message": "Invalid API key", "status": "error"}), 403

    # Send all data to Firebase
    try:
        response = requests.put(f"{FIREBASE_URL}/channels.json", json=channels_data)
        if response.status_code == 200:
            return jsonify({"message": "Data posted to Firebase successfully!", "status": "success"}), 200
        else:
            return jsonify({"message": "Failed to post data to Firebase", "status": "error"}), 500
    except Exception as e:
        return jsonify({"message": str(e), "status": "error"}), 500

# Save CSV headers if the file doesn't exist
if not os.path.exists("data.csv"):
    with open("data.csv", mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Channel", "Sensor Name", "Sensor Value", "Timestamp"])

if __name__ == '__main__':
    app.run(debug=True, port=5000)
