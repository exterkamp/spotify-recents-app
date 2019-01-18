import requests
import base64
import re
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
from google.cloud import storage
from functools import reduce
import json
import time
from random import shuffle
import os

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
        if track['uri'] in track_uri_set:
            continue
        track_uri_set.add(track['uri'])

        # check that there is a 300 x 300 album art file
        album = next((image['url'] for image in track['album']['images'] if image['height'] == 300 and image['width'] == 300), None)
        if album:
            track_data = {
                'name': track['name'],
                'artists': [{'name': artist['name']} for artist in track['artists']],
                'album': track['album']['name'],
                'album_art_url': album,
                'preview_url': track['preview_url'],
                'spotify_url': track['external_urls']['spotify'],
            }
            tracks.append(track_data)

    shuffle(tracks)

    # limit the tracks to 3
    if len(tracks) > 3:
        tracks = tracks[0:3]

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

    blob = bucket.get_blob(DATA_JSON_FILENAME)

    if blob:
        # file the old blob away
        updated_time = blob.updated
        bucket.copy_blob(
                blob, bucket, DATA_JSON_FILEPATH + "/" + str(updated_time) + "_" + DATA_JSON_FILENAME)
    else:
        blob = bucket.blob(DATA_JSON_FILENAME)

    # override the blob
    blob.upload_from_string(json.dumps(tracks_json), content_type='application/octet-stream')

if __name__ == "__main__":
    pubsub(None, None)