from flask import Flask
from flask import jsonify
from google.cloud import storage
import json
import datetime
import base64
from flask_cors import CORS

app = Flask(__name__)
cors = CORS(app, resources={r"/*": {"origins": "*"}})

@app.route('/recents', methods=['GET'])
def recents():
    client = storage.Client()
    bucket = client.get_bucket('spotify-cached-results')

    d = json.loads(bucket.get_blob("data.json").download_as_string().decode("utf-8"))

    return jsonify(d)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
