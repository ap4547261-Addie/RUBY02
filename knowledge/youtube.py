import urllib.request
import json

def get_video_metadata(video_url: str) -> dict:
    """Fetches oEmbed metadata for a YouTube video URL."""
    try:
        oembed_url = f"https://www.youtube.com/oembed?url={urllib.parse.quote(video_url)}&format=json"
        req = urllib.request.Request(oembed_url)
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))
            return {
                "title": data.get("title", "Unknown Title"),
                "author": data.get("author_name", "Unknown Author")
            }
    except Exception as e:
        return {"error": str(e)}
                              
