from flask import Flask, redirect, url_for, request
from flask import jsonify
from google.cloud import storage
import json
import datetime
import base64
from flask_cors import CORS
from google.cloud import datastore
from random import shuffle
# from google.cloud import firestore
# from datetime import datetime
# from datetime import timedelta
# from random import shuffle

app = Flask(__name__)
cors = CORS(app, resources={r"/*": {"origins": "*"}})

MAX_TRACKS = 25

client = datastore.Client()
query = client.query(kind='Track')

@app.route('/tracks', methods=['GET'])
def getTracks():
    count = min(int(request.args.get('count', default=1)), MAX_TRACKS)
    blacklist = request.args.get('blacklist', default=[])

    query.order = ['played_at']
    # fetch the last 25 entries, then we will prune from there
    entities = list(query.fetch(limit=MAX_TRACKS))
    tracks = []

    for entity in entities:
        track = {x: entity[x] for x in entity.keys()}
        track["uri"]= entity.key.name
        if track["uri"] not in blacklist:
            tracks.append(track)

    # shuffle the tracks
    shuffle(tracks)

    # limit the tracks to count
    if len(tracks) > count:
        tracks = tracks[0:count]

    return jsonify(tracks)

@app.route('/recents', methods=['GET'])
def recents():

    hour_ago = datetime.datetime.now() - datetime.timedelta(hours=6)
    # print(hour_ago.timestamp())
    query.order = ['played_at']
    # query.add_filter('played_at', '>=', hour_ago.timestamp())
    entities = list(query.fetch(limit=20))
    tracks = []

    for entity in entities:
        track = {x: entity[x] for x in entity.keys()}
        track["uri"]= entity.key.name
        tracks.append(track)

    # shuffle list and get 3
    shuffle(tracks)

    # limit the tracks to 3
    if len(tracks) > 3:
        tracks = tracks[0:3]

    return jsonify(tracks)

@app.route('/')
def greeting():
    return redirect(url_for('recents'))

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
