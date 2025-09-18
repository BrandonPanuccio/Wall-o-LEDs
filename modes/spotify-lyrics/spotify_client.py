import os
import time
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

load_dotenv()

class SpotifyClient:
    def __init__(self):
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=os.getenv("SPOTIFY_CLIENT_ID"),
            client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
            redirect_uri=os.getenv("SPOTIFY_REDIRECT_URI"),
            scope="user-read-playback-state user-read-currently-playing"
        ))

    def current_playback(self):
        pb = self.sp.current_playback()
        if not pb or not pb.get("item"):
            return None
        item = pb["item"]
        return {
            "id": item["id"],
            "name": item["name"],
            "artist": ", ".join(a["name"] for a in item["artists"]),
            "progress_ms": pb.get("progress_ms", 0),
            "is_playing": pb.get("is_playing", True),
        }
