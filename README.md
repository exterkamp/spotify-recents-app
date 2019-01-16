# Spotify Recents Cacher

This app powers my website's musical integration.

It is a basic GCP app that uses:
- [App Engine](https://cloud.google.com/appengine/)
- [Cloud Functions](https://cloud.google.com/functions/)
- [Storage](https://cloud.google.com/storage/)
- [Pub/Subs](https://cloud.google.com/pubsub/)
- [Cloud Endpoints](https://cloud.google.com/endpoints/)
- [Cloud Scheduler](https://cloud.google.com/scheduler/)
- [Spotify Web API](https://developer.spotify.com/documentation/web-api/)
    - [recents/ API](https://developer.spotify.com/documentation/web-api/reference/player/get-recently-played/)

```

  Client (website) -requests-> Cloud Functions API -reads-> Storage
                                                              ^
                                                              |
                                                           updates
                                                              |
Cloud Scheduler -publishes-> Pub/Sub Topic <-subscribed- Cloud Functions
                                                              |
                                                           requests
                                                              |
                                                              v
                                                      Spotify recents/ API

```