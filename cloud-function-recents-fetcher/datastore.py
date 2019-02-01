# from google.cloud import firestore

# db = firestore.Client()
# doc_ref = db.collection(u'spotify-tracks')

# docs = doc_ref.get()

# for doc in docs:
#     print(u'{} => {}'.format(doc.id, doc.to_dict()))
import requests
import base64
import re
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
from google.cloud import storage
from google.cloud import datastore
from functools import reduce
import json
import time
from random import shuffle
import os
import uuid
import datetime

def pubsub(event, context):
    clientId = os.environ.get('clientId', 'Specified environment variable is not set.')
    clientSecret = os.environ.get('clientSecret', 'Specified environment variable is not set.')
    refreshToken = os.environ.get('refreshToken', 'Specified environment variable is not set.')

    DATA_JSON_FILENAME = os.environ.get('DATA_JSON_FILENAME', 'Specified environment variable is not set.')
    DATA_JSON_FILEPATH = os.environ.get('DATA_JSON_FILEPATH', 'Specified environment variable is not set.')
	
    BUCKET_NAME = os.environ.get('BUCKET_NAME', 'Specified environment variable is not set.')
    
    clientAuth = clientId + ':' + clientSecret

    client = storage.Client()
    bucket = client.get_bucket(BUCKET_NAME)

    client = datastore.Client()

    headers = {'Authorization': 'Basic ' + base64.b64encode(clientAuth.encode()).decode('utf-8')}
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': refreshToken,
        'scope': 'user-read-recently-played',
    }
    r = requests.post('https://accounts.spotify.com/api/token', headers=headers, data=data)
    response = r.json()
    access_token = response['access_token']

    headers_bearer = {'Authorization': 'Bearer ' + access_token}
    params = {
        'limit': 25
    }
    r = requests.get('https://api.spotify.com/v1/me/player/recently-played', headers=headers_bearer, params=params)

    recents = r.json()
    tracks = []
    track_uri_set = set()

    for item in recents['items']:
        track = item['track']

        played_at = datetime.datetime.strptime(item['played_at'], '%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=datetime.timezone.utc).timestamp()
        
        if track['uri'] in track_uri_set:
            continue
        track_uri_set.add(track['uri'])

        # check that there is a 300 x 300 album art file
        album = next((image['url'] for image in track['album']['images'] if image['height'] == 300 and image['width'] == 300), None)
        if album:
            track_data = {
                'uri': track['uri'],
                'name': track['name'],
                'artists': [{'name': artist['name']} for artist in track['artists']],
                'album': track['album']['name'],
                'album_art_url': album,
                'preview_url': track['preview_url'],
                'spotify_url': track['external_urls']['spotify'],
                'played_at': played_at,
            }
            tracks.append(track_data)

    shuffle(tracks)

    # limit the tracks to 3
    if len(tracks) > 10:
        tracks = tracks[0:10]

    for track in tracks:
        r = requests.get(track['album_art_url'])
        img = Image.open(BytesIO(r.content))
        # resize to 150px
        basewidth = 150
        wpercent = (basewidth/float(img.size[0]))
        hsize = int((float(img.size[1])*float(wpercent)))
        img = img.resize((basewidth,hsize), Image.ANTIALIAS)

        # encode to base64
        buffered = BytesIO()
        img.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue())
        track['album_art_encoded'] = img_str.decode()

    tracks_json = {
        'update_time': int(round(time.time() * 1000)),
        'tracks': tracks,
    }

    # lets play with some datastore!
    for track in tracks_json['tracks']:
        key = client.key('Track', track['uri'])
        entity = datastore.Entity(key=key)
        trackClone = track
        blob = bucket.get_blob(track['uri'])

        if not blob:
            blob = bucket.blob(track['uri'])

        # override the blob
        blob.upload_from_string(track['album_art_encoded'], content_type='application/octet-stream')
        del trackClone["album_art_encoded"]
        entity.update(trackClone)
        client.put(entity)

if __name__ == "__main__":
    pubsub(None, None)