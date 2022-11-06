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


class LastPath(HTTPConnection):
    @property
    def last_path(self) -> dict:
        assert (
            "last_path" in self.scope
        ), "SessionMiddleware must be installed to access request.last_path"
        return self.scope["last_path"]


# Entry point
if __name__ == '__main__':
    uvicorn.run(
        'server:app', port=443, host='0.0.0.0',
        #reload=True,
        #reload_dirs=['.'],
        ssl_keyfile=config['SSL_KEYFILE'],
        ssl_certfile=config['SSL_CERTFILE']
    )


def credentials_to_dict(credentials):
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }


@app.get("/authorize")
async def authorize(request: Request):
    # Create flow instance to manage the OAuth 2.0 Authorization Grant Flow steps.
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES
    )

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

    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES, state=state
    )
    flow.redirect_uri = request.url_for('oauth2callback')

    # Use the authorization server's response to fetch the OAuth 2.0 tokens.
    authorization_response = request.url
    flow.fetch_token(authorization_response=authorization_response.__str__())

    # Store credentials in the session.
    # ACTION ITEM: In a production app, you likely want to save these credentials in a persistent database instead.
    credentials = flow.credentials
    request.session['credentials'] = credentials_to_dict(credentials)

    return RedirectResponse(app.url_path_for(request.session['last_path']))


@app.get('/revoke')
def revoke(request: Request):
    if 'credentials' not in request.session:
        return {"message": "You need to authorize before testing the code to revoke credentials."}

    credentials = google.oauth2.credentials.Credentials(
        **request.session['credentials']
    )

    revoke = requests.post(
        'https://oauth2.googleapis.com/revoke',
        params={'token': credentials.token},
        headers={'content-type': 'application/x-www-form-urlencoded'}
    )

    status_code = getattr(revoke, 'status_code')
    if status_code == 200:
        return {"message": "Credentials successfully revoked."}
    else:
        return {"message": "An error occurred."}


@app.get('/clear')
def clear_credentials(request: Request):
    if 'credentials' in request.session:
        del request.session['credentials']

    if 'last_path' in request.session:
        del request.session['last_path']

    return RedirectResponse(app.url_path_for('root'))


@app.get('/channel')
def channel(request: Request):
    if 'credentials' not in request.session:
        request.session['last_path'] = channel.__name__
        return RedirectResponse(app.url_path_for('authorize'))

    # Load credentials from the session.
    credentials = YouTubeHandler.read_credentials(request.session['credentials'])

    youtube = googleapiclient.discovery.build(
        API_SERVICE_NAME, API_VERSION, credentials=credentials
    )

    channel = youtube.channels().list(mine=True, part='snippet,contentDetails').execute()

    # Save credentials back to session in case access token was refreshed.
    # ACTION ITEM: In a production app, you likely want to save these credentials in a persistent database instead.
    request.session['credentials'] = credentials_to_dict(credentials)

    return channel


@app.get('/playlists')
def playlists(request: Request):
    if 'credentials' not in request.session:
        request.session['last_path'] = playlists.__name__
        return RedirectResponse(app.url_path_for('authorize'))

    # Load credentials from the session.
    credentials = google.oauth2.credentials.Credentials(
        **request.session['credentials']
    )

    youtube = googleapiclient.discovery.build(
        API_SERVICE_NAME, API_VERSION, credentials=credentials
    )

    playlists = youtube.playlists().list(
        part="snippet,contentDetails",
        maxResults=25,
        mine=True
    ).execute()

    # Save credentials back to session in case access token was refreshed.
    # ACTION ITEM: In a production app, you likely want to save these credentials in a persistent database instead.
    request.session['credentials'] = credentials_to_dict(credentials)

    return playlists


@app.get("/")
async def root(request: Request):
    return {"root": "Welcome to FAYT"}