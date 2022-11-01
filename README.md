# YouTube FastAPI wrapper

I have my own little YouTube channel (https://youtube.com/@darxyde), and I just realised there is no easy way to rename multiple videos in an ordered way like you would with your mp3 files for example.

YouTube provides an API to manage the videos, and as such I think this could be an interesting project to do.

My plan is to use Python and fastAPI to create a wrapper around YouTube's own api.

## Prerequisites

- Python 3.9+
- The `pip` package management tool
- The Google APIs Client Library for Python:

    `pip install --upgrade google-api-python-client`
- The google-auth-oauthlib and google-auth-httplib2 libraries for user authorization

    `pip install --upgrade google-auth-oauthlib google-auth-httplib2`

- FastAPI

    `pip install fastapi`
- Uvicorn
    
    `pip install "uvicorn[standard]"`

### Links
[YouTube Data API](https://developers.google.com/youtube/v3/quickstart/python)

[FastAPI](https://fastapi.tiangolo.com/)