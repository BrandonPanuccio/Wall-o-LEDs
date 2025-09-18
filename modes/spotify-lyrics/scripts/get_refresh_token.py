import os
from urllib.parse import urlparse, parse_qs

from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth

# Loads SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_REDIRECT_URI from .env
load_dotenv()

SCOPES = "user-read-currently-playing user-read-playback-state"

def main():
    sp_oauth = SpotifyOAuth(
        scope=SCOPES,
        client_id=os.getenv("SPOTIFY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
        redirect_uri=os.getenv("SPOTIFY_REDIRECT_URI"),
        open_browser=True,            # opens your browser for login/consent
        cache_path=None               # don’t cache to .cache by default
    )

    # 1) Build auth URL & open browser; 2) local HTTP server catches the redirect with ?code=
    # If local server fails (rare on some setups), it will print a URL for you to paste back.
    code = sp_oauth.get_auth_response(open_browser=True)

    # Exchange code for tokens
    token_info = sp_oauth.get_access_token(code, as_dict=True)
    refresh = token_info.get("refresh_token")
    access = token_info.get("access_token")

    if not refresh:
        raise SystemExit("No refresh_token returned. In the Spotify dialog, be sure you approved the scopes.")

    print("\n✅ Success!")
    print("Your refresh token (save this in your .env as SPOTIFY_REFRESH_TOKEN):\n")
    print(refresh)
    print("\n(Access token is temporary; you don’t need to save it.)")

if __name__ == "__main__":
    main()
