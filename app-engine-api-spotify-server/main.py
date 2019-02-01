from flask import Flask, redirect, url_for
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

# db = firestore.Client()
# tracks = db.collection('spotify-tracks')

# client = storage.Client()
# bucket = client.get_bucket('spotify-cached-results')

client = datastore.Client()
query = client.query(kind='Track')

@app.route('/recents', methods=['GET'])
def recents():

    hour_ago = datetime.datetime.now() - datetime.timedelta(hours=6)
    # print(hour_ago.timestamp())
    query.order = ['played_at']
    # query.add_filter('played_at', '>=', hour_ago.timestamp())
    entities = list(query.fetch(limit=25))
    tracks = []

    for entity in entities:
        track = {x: entity[x] for x in entity.keys()}
        track["uri"]= entity.key.name
        tracks.append(track)
    # d = json.loads(bucket.get_blob("data.json").download_as_string().decode("utf-8"))

    # # docs = db.collection('spotify-tracks').where('updated', '>', datetime.now() - timedelta(hours=1)).get()

    # return jsonify(d)
    # # docs = tracks.order_by('updated').limit(20).get()

    # ret = []

    # for doc in docs:
    #     ret.append(doc.to_dict())
    #     # rint(u'{} => {}'.format(doc.id, doc.to_dict()))

    # shuffle(ret)

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
