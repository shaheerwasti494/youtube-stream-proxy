from flask import Flask, request, redirect
from yt_dlp import YoutubeDL
from cachetools import TTLCache
import re

app = Flask(__name__)
cache = TTLCache(maxsize=1000, ttl=300)  # Cache up to 1000 items for 5 minutes

@app.route("/stream")
def stream():
    raw_id = request.args.get("id")
    if not raw_id:
        return "Missing id parameter", 400

    # Sanitize and extract only the 11-character YouTube video ID
    match = re.search(r"([a-zA-Z0-9_-]{11})", raw_id)
    video_id = match.group(1) if match else None

    if not video_id:
        return "Invalid video ID", 400

    if video_id in cache:
        return redirect(cache[video_id], code=302)

    try:
        ydl_opts = {
            "quiet": True,
            "skip_download": True,
            "force_generic_extractor": False
        }

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://youtu.be/{video_id}", download=False)
            formats = info.get("formats", [])

            # Prefer exact 720p MP4 with both audio and video
            format_720p = next(
                (f for f in formats if f.get("ext") == "mp4" and f.get("height") == 720
                 and f.get("acodec") != "none" and f.get("vcodec") != "none"),
                None
            )

            # Fallback: best available MP4 with audio + video
            if not format_720p:
                progressive = [f for f in formats if f.get("ext") == "mp4"
                               and f.get("acodec") != "none" and f.get("vcodec") != "none"]
                format_720p = max(progressive, key=lambda x: x.get("height", 0), default=None)

            if not format_720p:
                return "No playable MP4 format found", 404

            stream_url = format_720p["url"]
            cache[video_id] = stream_url
            return redirect(stream_url, code=302)

    except Exception as e:
        return f"Error: {str(e)}", 500


@app.route("/")
def home():
    return "✅ YouTube Stream Proxy is running on Flask!"


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
