# main.py
import os
import time
import asyncio
from typing import Dict, List, Tuple
from dotenv import load_dotenv

from spotify_client import SpotifyClient
from lyrics_provider import fetch_lyrics
from lrc_parser import parse_lrc

load_dotenv()

# Positive = delay lyrics (show later). Negative = show earlier.
CAL_OFFSET_MS = int(os.getenv("LYRICS_TIME_OFFSET_MS", "120"))
# How often we re-sync with Spotify progress
SPOTIFY_POLL_HZ = float(os.getenv("SPOTIFY_POLL_HZ", "2.0"))

LyricsLines = List[Tuple[int, str]]

class LyricsSession:
    """
    Holds per-track printing state.
    """
    def __init__(self, track_id: str, lines: LyricsLines):
        self.track_id = track_id
        self.lines = lines
        self.fired = [False] * len(lines)  # which lines have been printed

    def reset(self, lines: LyricsLines):
        self.lines = lines
        self.fired = [False] * len(lines)

async def build_lines_for_track(artist: str, title: str) -> LyricsLines:
    lrc = await fetch_lyrics(artist, title)
    if not lrc:
        return []  # no lyrics
    lines = parse_lrc(lrc)
    return lines

async def run_loop():
    sp = SpotifyClient()

    cache: Dict[str, LyricsLines] = {}   # track_id -> parsed lines
    session: LyricsSession | None = None
    last_track_id: str | None = None
    next_tick = time.monotonic()

    print("🎵 Lyrics follower started. Skip/pause/seek in Spotify and watch this follow.")

    while True:
        pb = sp.current_playback()
        if not pb or not pb.get("id"):
            # Nothing playing; small idle sleep
            await asyncio.sleep(0.4)
            continue

        track_id = pb["id"]
        title = pb["name"]
        artist = pb["artist"]
        progress_ms = pb.get("progress_ms", 0)
        is_playing = pb.get("is_playing", True)

        # Track changed?
        if track_id != last_track_id:
            print(f"\nNow playing: {artist} - {title}")
            # Pull from cache or fetch once
            if track_id not in cache:
                cache[track_id] = await build_lines_for_track(artist, title)
            session = LyricsSession(track_id, cache[track_id])
            last_track_id = track_id

        # If we still have no session (unlikely) or no lyrics, just idle until next song
        if not session or len(session.lines) == 0:
            if session is not None and len(session.lines) == 0:
                # Plain lyrics case: we printed nothing yet; print raw once
                # (Optional: you could print the raw text here, but keeping console quiet is cleaner)
                pass
            # pace loop
            next_tick += 1.0 / SPOTIFY_POLL_HZ
            await asyncio.sleep(max(0, next_tick - time.monotonic()))
            continue

        # Apply calibration offset
        now_ms = (progress_ms + CAL_OFFSET_MS)

        # Print any lines whose timestamp is <= now_ms and not yet printed
        for i, (ts, text) in enumerate(session.lines):
            if not session.fired[i] and ts <= now_ms:
                print(text)
                session.fired[i] = True

        # If user **seeks backwards**, un-fire lines ahead of new position
        # (e.g., dragged the time bar back)
        for i, (ts, _) in enumerate(session.lines):
            if session.fired[i] and ts > now_ms + 250:  # small hysteresis window
                session.fired[i] = False

        # All lines printed? We’ll keep polling—if you seek back, lines will re-print as needed.
        # pace / re-sync cadence
        if not is_playing:
            # paused—poll a little faster so we resume quickly
            await asyncio.sleep(0.25)
        else:
            next_tick += 1.0 / SPOTIFY_POLL_HZ
            await asyncio.sleep(max(0, next_tick - time.monotonic()))

if __name__ == "__main__":
    asyncio.run(run_loop())
