"""Explicit local OAuth consent. Persist refresh token only in backend/.env."""
import os
from dotenv import set_key
from google_auth_oauthlib.flow import InstalledAppFlow
from app.youtube import ENV_PATH, settings

def main():
    config = settings()
    if not config.get('YOUTUBE_CLIENT_ID') or not config.get('YOUTUBE_CLIENT_SECRET'):
        raise SystemExit('Set the Desktop client ID and secret in backend/.env first.')
    flow = InstalledAppFlow.from_client_config({'installed': {
        'client_id': config['YOUTUBE_CLIENT_ID'], 'client_secret': config['YOUTUBE_CLIENT_SECRET'],
        'auth_uri': 'https://accounts.google.com/o/oauth2/auth', 'token_uri': 'https://oauth2.googleapis.com/token',
    }}, scopes=['https://www.googleapis.com/auth/youtube.readonly', 'https://www.googleapis.com/auth/yt-analytics.readonly'],
        autogenerate_code_verifier=True)
    credentials = flow.run_local_server(host='127.0.0.1', port=0, open_browser=True, prompt='consent',
        timeout_seconds=180, authorization_prompt_message='Opening Google consent in your browser.',
        success_message='Authorization complete. Close this window.')
    if not credentials.refresh_token:
        raise SystemExit('No refresh token returned. Revoke access and authorize again.')
    os.chmod(ENV_PATH, 0o600)
    set_key(str(ENV_PATH), 'YOUTUBE_REFRESH_TOKEN', credentials.refresh_token)
    os.chmod(ENV_PATH, 0o600)
    print('Credentials saved to backend/.env. Set YOUTUBE_CHANNEL_ID, then sync.')

if __name__ == '__main__':
    try:
        main()
    except Exception:
        raise SystemExit('OAuth setup failed. Check Desktop client configuration and retry.') from None
