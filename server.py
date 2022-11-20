from models import *
from dotenv import dotenv_values
from starlette.middleware.sessions import SessionMiddleware

from fastapi import FastAPI
from fastapi.requests import HTTPConnection, Request
from fastapi.responses import RedirectResponse
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery

import uvicorn
import requests

config = dotenv_values("./env/.env")

CLIENT_SECRETS_FILE = config['YT_CLIENT_SECRET_JSON']
SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']
API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'


# Main app
app = FastAPI(
    title=config['APP_TITLE'],
    description=config['APP_DESCRIPTION'],
    version="0.0.1",
    contact={
        "name": config['CONTACT_NAME'],
        "url": config['CONTACT_URL'],
        "email": config['CONTACT_EMAIL'],
    },
    openapi_url=config['OPENAPI_URL'],
    docs_url=config['DOCS_URL'],
    redoc_url=None
)
app.add_middleware(HTTPSRedirectMiddleware)
app.add_middleware(SessionMiddleware, secret_key=config['APP_SECRET_KEY'])

# Add the last path to the session
class LastPath(HTTPConnection):
    @property
    def last_path(self) -> dict:
        assert (
            "last_path" in self.scope
        ), "SessionMiddleware must be installed to access request.last_path"
        return self.scope["last_path"]


def get_credentials(request: Request):    
    return google.oauth2.credentials.Credentials(**request.session['credentials'])


def set_credentials(request: Request, credentials: str):
    request.session['credentials'] = credentials_to_dict(credentials)


def get_youtube(credentials: str):
    return googleapiclient.discovery.build(API_SERVICE_NAME, API_VERSION, credentials=credentials)


def clear_session(request: Request):
    if 'credentials' in request.session:
        del request.session['credentials']

    if 'last_path' in request.session:
        del request.session['last_path']


def credentials_to_dict(credentials):
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }


# Entry point
if __name__ == '__main__':
    uvicorn.run(
        'server:app', port=443, host='0.0.0.0',
        reload=True,
        #reload_dirs=['.'],
        ssl_keyfile=config['SSL_KEYFILE'],
        ssl_certfile=config['SSL_CERTFILE']
    )


@app.get("/")
async def root(request: Request):
    return {"root": config['APP_TITLE']}


@app.get("/authorize")
async def authorize(request: Request):
    # Create flow instance to manage the OAuth 2.0 Authorization Grant Flow steps.
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(CLIENT_SECRETS_FILE, scopes=SCOPES)

    # The URI created here must exactly match one of the authorized redirect URIs for the OAuth 2.0 client, which you configured in the API Console. If this
    # value doesn't match an authorized URI, you will get a 'redirect_uri_mismatch' error
    flow.redirect_uri = request.url_for('oauth2callback')

    authorization_url, state = flow.authorization_url(
        # Enable offline access so that you can refresh an access token without re-prompting the user for permission. Recommended for web server apps.
        access_type='offline',
        # Enable incremental authorization. Recommended as a best practice.
        include_granted_scopes='true'
    )

    # Store the state so the callback can verify the auth server response.
    request.session['state'] = state

    # return request.redirect(authorization_url)
    return RedirectResponse(authorization_url)


@app.get('/oauth2callback')
async def oauth2callback(request: Request):
    state = request.session['state']

    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(CLIENT_SECRETS_FILE, scopes=SCOPES, state=state)
    flow.redirect_uri = request.url_for('oauth2callback')

    # Use the authorization server's response to fetch the OAuth 2.0 tokens.
    authorization_response = request.url
    flow.fetch_token(authorization_response=authorization_response.__str__())

    # Store credentials in the session.
    # ACTION ITEM: In a production app, you likely want to save these credentials in a persistent database instead.
    set_credentials(request, flow.credentials)

    return RedirectResponse(app.url_path_for(request.session.get('last_path', 'root')))


@app.get('/revoke')
async def revoke(request: Request):
    if 'credentials' not in request.session:
        return {"message": "You need to authorize before testing the code to revoke credentials."}

    credentials = get_credentials(request)

    revoke = requests.post(
        'https://oauth2.googleapis.com/revoke',
        params={'token': credentials.token},
        headers={'content-type': 'application/x-www-form-urlencoded'}
    )

    clear_session(request)

    status_code = getattr(revoke, 'status_code')
    if status_code == 200:
        return {"message": "Credentials successfully revoked."}
    else:
        return {"message": "An error occurred."}


@app.get('/clear')
async def clear_credentials(request: Request):
    clear_session(request)

    return RedirectResponse(app.url_path_for('root'))


@app.get('/channel', response_model=ChannelRoot)
async def get_channel(request: Request):
    if 'credentials' not in request.session:
        request.session['last_path'] = get_channel.__name__
        return RedirectResponse(app.url_path_for('authorize'))

    # Load credentials from the session.
    credentials = get_credentials(request)

    youtube = get_youtube(credentials)

    channel = youtube.channels().list(
        part='snippet,contentDetails',
        mine=True
    ).execute()

    # Save credentials back to session in case access token was refreshed.
    # ACTION ITEM: In a production app, you likely want to save these credentials in a persistent database instead.
    set_credentials(request, credentials)

    return channel


@app.get('/playlists', response_model=PlaylistRoot)
async def get_playlists(request: Request, next_page: str = None, results_per_page: int = 25):
    if 'credentials' not in request.session:
        request.session['last_path'] = get_playlists.__name__
        return RedirectResponse(app.url_path_for('authorize'))

    # Load credentials from the session.
    credentials = get_credentials(request)

    youtube = get_youtube(credentials)

    playlists = youtube.playlists().list(
        part="snippet,contentDetails",
        maxResults=results_per_page,
        mine=True,
        pageToken=next_page
    ).execute()

    # Save credentials back to session in case access token was refreshed.
    # ACTION ITEM: In a production app, you likely want to save these credentials in a persistent database instead.
    set_credentials(request, credentials)

    return playlists


@app.get('/videos', response_model=VideoRoot)
async def get_videos(request: Request, next_page: str = None, results_per_page: int = 25):
    if 'credentials' not in request.session:
        request.session['last_path'] = get_videos.__name__
        return RedirectResponse(app.url_path_for('authorize'))

    # Load credentials from the session.
    credentials = get_credentials(request)

    youtube = get_youtube(credentials)

    videos = youtube.search().list(
        part="snippet",
        forMine=True,
        maxResults=results_per_page,
        type="video",
        pageToken=next_page
    ).execute()

    # Save credentials back to session in case access token was refreshed.
    # ACTION ITEM: In a production app, you likely want to save these credentials in a persistent database instead.
    set_credentials(request, credentials)

    return videos