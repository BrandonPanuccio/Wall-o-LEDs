# Spotify Lyrics (console mode)

This mode follows your current Spotify playback and prints **time-synced lyrics** to the console in real time. It also shows a one-line **status ticker**: play/pause, progress, total duration, and how many lyric lines have been printed.

> Later we’ll swap the console renderer for the LED panel renderer; the sync logic stays the same.

---

## Prereqs

- Python 3.11+ on Linux/WSL or Raspberry Pi OS
- `python3-venv` package (Ubuntu/WSL):  
  ```bash
  sudo apt update && sudo apt install -y python3-venv

## 1. Create venv & install deps

cd ~/git/Wall-o-LEDs/modes/spotify-lyrics
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt


## 2. Create .env from the example

## .env
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
SPOTIFY_REDIRECT_URI=http://127.0.0.1:8080/callback
SPOTIFY_REFRESH_TOKEN=   # fill this in after step 3

# Lyrics provider
PRIMARY_LYRICS_PROVIDER=lrclib

# delay (positive) or advance (negative) lyrics globally
LYRICS_TIME_OFFSET_MS=120
# how often to poll Spotify (higher = tighter sync, more API calls)
SPOTIFY_POLL_HZ=3.0


## 3. Get a refresh token (one-time)

python scripts/get_refresh_token.py


Log in & approve scopes in the browser.

Paste the printed refresh token into SPOTIFY_REFRESH_TOKEN in .env.

## 4. Run

With helper script:

./run.sh

## 5. Stop

./stop.sh
