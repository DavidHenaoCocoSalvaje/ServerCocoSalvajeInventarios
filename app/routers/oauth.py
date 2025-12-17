from datetime import datetime, timezone
from typing import cast
from fastapi import APIRouter, Request
from authlib.integrations.starlette_client import OAuth, StarletteOAuth2App
from fastapi.responses import RedirectResponse
from app.config import Config
import json
from google.oauth2.credentials import Credentials


def get_credentials_google(path_file_credentials_json: str) -> tuple[str, str] | tuple[None, None]:
    """
    Obtiene las credenciales de Google desde un archivo JSON.

    Args:
        path_file_credentials_json (str): Ruta al archivo JSON de credenciales.

    Returns:
        tuple[str, str] | tuple[None, None]: Un tuple con el ID y el secreto de la aplicación, o None si hay un error.
    """
    try:
        with open(path_file_credentials_json, 'r') as f:
            credentials = json.load(f)
            web = credentials.get('web') or credentials.get('installed')
            if not web:
                print("El archivo de credenciales no tiene la sección 'web' o 'installed'.")
                return None, None
            return web.get('client_id'), web.get('client_secret')
    except FileNotFoundError:
        print(f'Error: No se encontró el archivo {path_file_credentials_json}.')
        return None, None
    except Exception as e:
        print(f'Error al cargar {path_file_credentials_json}: {e}')
        return None, None


user_scopes = [
    'openid',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
]
gmail_scopes = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.metadata',
]


client_id, client_secret = get_credentials_google('credentials/integraciones-coco.json')
if client_id is None or client_secret is None:
    raise ValueError('No se pudieron obtener las credenciales de Google.')

if Config.environment in ['production', 'prod']:
    redirect_uri = 'https://api.cocosalvajeapps.com/oauth/google/callback'
else:
    redirect_uri = 'http://localhost:8000/oauth/google/callback'

oauth = OAuth()
oauth.register(
    name='google',
    client_id=client_id,
    client_secret=client_secret,
    redirect_uri=redirect_uri,
    authorization_endpoint='https://accounts.google.com/o/oauth2/v2/auth',
    token_endpoint='https://oauth2.googleapis.com/token',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': ' '.join(user_scopes + gmail_scopes)},
)
google_oauth_client = oauth.register(name='google')
router = APIRouter(prefix='/oauth', tags=['oauth'])


def build_google_credentials_from_token(token: dict) -> Credentials:
    """
    Construye google.oauth2.credentials.Credentials a partir del token de Authlib.
    """
    # token puede traer expires_at (epoch) o expires_in. google-auth usa datetime.
    expire = None
    if token.get('expires_at'):
        try:
            expire = datetime.fromtimestamp(token['expires_at'], tz=timezone.utc)
        except Exception:
            expire = None

    creds = Credentials(
        token=token.get('access_token'),
        refresh_token=token.get('refresh_token'),
        token_uri='https://oauth2.googleapis.com/token',
        client_id=client_id,
        client_secret=client_secret,
        scopes=user_scopes + gmail_scopes,
    )

    # Adjuntar expiry si lo tenemos (opcional, google-auth refresca cuando falle)
    if expire is not None:
        try:
            creds.expiry = expire
        except Exception:
            pass

    return creds


@router.get('/google/authorize')
async def authorize(request: Request):
    google_client = cast(StarletteOAuth2App, oauth.google)
    return await google_client.authorize_redirect(request, redirect_uri)


@router.get('/google/callback')
async def callback(request: Request):
    google_client = cast(StarletteOAuth2App, oauth.google)

    token = await google_client.authorize_access_token(request)
    request.session['google_token'] = token

    return RedirectResponse(url='https://cocosalvajeapps.com', status_code=302)
