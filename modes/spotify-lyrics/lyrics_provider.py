import httpx

async def fetch_lyrics(artist, title):
    url = f"https://lrclib.net/api/get?artist_name={artist}&track_name={title}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("syncedLyrics") or data.get("plainLyrics")
    return None
