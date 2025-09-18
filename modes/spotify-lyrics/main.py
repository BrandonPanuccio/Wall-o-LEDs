# main.py — lyrics-only console renderer with non-blocking typewriter + colors
# - follows skips/seeks
# - no overlapping status line
# - tolerant to different parse_lrc() return shapes

import os
import time
import asyncio
from typing import Dict, List, Tuple, Optional
from dotenv import load_dotenv

from spotify_client import SpotifyClient
from lyrics_provider import fetch_lyrics
from lrc_parser import parse_lrc
from colors import apply_theme

load_dotenv()

# Config (set in .env)
CAL_OFFSET_MS   = int(os.getenv("LYRICS_TIME_OFFSET_MS", "120"))
SPOTIFY_POLL_HZ = float(os.getenv("SPOTIFY_POLL_HZ", "2.5"))
KARAOKE_MODE    = os.getenv("KARAOKE_MODE", "typewriter").lower()   # "typewriter" | "off"
KARAOKE_CPS     = int(os.getenv("KARAOKE_CPS", "24"))
THEME           = os.getenv("THEME", "plain").lower()
DEBUG           = os.getenv("DEBUG", "0") == "1"

LyricsLines = List[Tuple[int, str]]

def _chars_revealed(text: str, elapsed_ms: int) -> int:
    """How many characters should be visible given elapsed time and CPS."""
    if KARAOKE_CPS <= 0:
        return len(text)
    return max(0, min(len(text), int(elapsed_ms * KARAOKE_CPS / 1000)))

def _safe_parse_lrc(text: str) -> LyricsLines:
    """
    Call parse_lrc(text) and accept 1/2/3-element tuples or a plain list.
    Always return a list of (timestamp_ms, line_text).
    """
    result = parse_lrc(text)
    # parse_lrc may return: lines, (lines, word_map), or (lines, word_map, meta)
    if isinstance(result, tuple):
        if len(result) >= 1:
            return result[0] or []
        # unusual: empty tuple -> no lines
        return []
    # or it could just be the list directly
    return result or []

async def run_loop():
    sp = SpotifyClient()

    # Cache lyrics per track_id: (lines, plain_text_if_no_lrc)
    cache: Dict[str, Tuple[LyricsLines, Optional[str]]] = {}

    last_track_id: Optional[str] = None
    lines: LyricsLines = []
    plain_text: Optional[str] = None

    # Per-track rendering state
    printed: Dict[int, bool] = {}   # line_ts -> printed?
    active_idx: int = -1
    in_partial_render: bool = False # whether we're repainting current line with \r

    print("🎵 Lyrics follower started. (Ctrl+C to quit)\n")

    next_tick = time.monotonic()
    while True:
        pb = sp.current_playback()
        if not pb or not pb.get("id"):
            await asyncio.sleep(0.4)
            continue

        track_id = pb["id"]
        title = pb["name"]
        artist = pb["artist"]
        progress_ms = pb.get("progress_ms", 0) or 0
        is_playing = pb.get("is_playing", True)

        # Track change?
        if track_id != last_track_id:
            # finalize any partial line from previous track
            if in_partial_render:
                print()
                in_partial_render = False

            print(f"\nNow playing: {artist} - {title}")

            if track_id not in cache:
                text = await fetch_lyrics(artist, title)
                if text:
                    lns = _safe_parse_lrc(text)
                    cache[track_id] = (lns, None if lns else text)
                else:
                    cache[track_id] = ([], None)

            lines, plain_text = cache[track_id]
            printed = {ts: False for ts, _ in lines}
            active_idx = -1
            last_track_id = track_id

            if DEBUG:
                if lines:
                    print(f"[debug] loaded {len(lines)} synced lines")
                elif plain_text:
                    print(f"[debug] plain-only lyrics (~{len(plain_text.splitlines())} lines)")
                else:
                    print("[debug] no lyrics available")

            # Plain-only: print once so user sees something
            if plain_text and not lines:
                print(plain_text.strip())

        # If we have synced lines, compute a snapshot (non-blocking)
        if lines:
            now_ms = progress_ms + CAL_OFFSET_MS

            # find the latest line whose ts <= now_ms
            new_active = -1
            for i, (ts, _text) in enumerate(lines):
                if ts <= now_ms:
                    new_active = i
                else:
                    break

            # if line changed (or user seeks), finalize old partial with newline
            if in_partial_render and (new_active != active_idx):
                print()
                in_partial_render = False

            active_idx = new_active

            # print any fully due lines before the active line
            if active_idx >= 0:
                for i in range(0, active_idx):
                    ts, text = lines[i]
                    if not printed[ts] and ts <= now_ms:
                        print(apply_theme(text, THEME))
                        printed[ts] = True

                # active line snapshot
                ts, text = lines[active_idx]
                elapsed = max(0, now_ms - ts)

                if KARAOKE_MODE == "typewriter" and is_playing:
                    count = _chars_revealed(text, elapsed)
                    partial = text[:count]
                    if not printed[ts]:
                        # start a repaintable line once
                        print()
                        printed[ts] = True
                    # repaint current line in place
                    themed = apply_theme(partial, THEME, rainbow_step=int(elapsed/40))
                    print("\r" + themed, end="", flush=True)
                    in_partial_render = True
                else:
                    # not typewriter: print full line once
                    if not printed[ts] and ts <= now_ms:
                        print(apply_theme(text, THEME))
                        printed[ts] = True
                        in_partial_render = False

                # If user seeks backward, re-arm future lines so they can print again when reached
                for ts2, _t2 in lines:
                    if printed.get(ts2) and ts2 > now_ms + 250:
                        printed[ts2] = False

        # pace polling
        next_tick += 1.0 / SPOTIFY_POLL_HZ
        await asyncio.sleep(max(0, next_tick - time.monotonic()))

if __name__ == "__main__":
    try:
        asyncio.run(run_loop())
    except KeyboardInterrupt:
        print("\nExiting…")
