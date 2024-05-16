from flask import Flask, request, jsonify
import json
import os
import outlier_detection_DBScan as od # Outlier Detection
from threading import Thread
app = Flask(__name__)

DATA_DIRECTORY = "Data"
valid_token = '[SECRET]'
json_filename = "received_data.json"
data_list = [] 

@app.route('/', methods=['POST'])
def receive_data():
    token = request.headers.get('Token')
    if token == valid_token:
        received_data = json.loads(request.data.decode("utf-8"))
        if not os.path.exists(DATA_DIRECTORY):
            os.makedirs(DATA_DIRECTORY)
        json_log_file = os.path.join(DATA_DIRECTORY,json_filename)
        existing_data = []
        if os.path.exists(json_log_file):
            with open(json_log_file, 'r') as json_file:
                existing_data = json.load(json_file)
        existing_data.append(received_data)
        with open(json_log_file, 'w') as json_file:
            json.dump(existing_data, json_file, indent=2)
        # Calculates new Clusters with Hamming Distance
        t1 = Thread(target=od.new_entry)
        t1.start()
        return jsonify({'message': 'Daten erfolgreich empfangen und gespeichert.'}), 200
    else:
        return jsonify({'message': 'Token ungültig. Daten wurden verworfen.'}), 401

if __name__ == '__main__':
    app.run()