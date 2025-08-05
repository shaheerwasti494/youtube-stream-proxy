from flask import Flask, request, redirect
from yt_dlp import YoutubeDL
from cachetools import TTLCache

app = Flask(__name__)
cache = TTLCache(maxsize=1000, ttl=300)  # Cache for 5 minutes

@app.route("/stream")
def stream():
    video_id = request.args.get("id")
    if not video_id:
        return "Missing id parameter", 400

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

            # Prefer 720p MP4 with both audio & video
            stream_720p = next(
                (f for f in formats if f.get("ext") == "mp4" and f.get("height") == 720 and f.get("acodec") != "none" and f.get("vcodec") != "none"),
                None
            )

            if not stream_720p:
                progressive_mp4s = [f for f in formats if f.get("ext") == "mp4" and f.get("acodec") != "none" and f.get("vcodec") != "none"]
                stream_720p = max(progressive_mp4s, key=lambda x: x.get("height", 0), default=None)

            if not stream_720p:
                return "No playable MP4 stream found.", 404

            stream_url = stream_720p["url"]
            cache[video_id] = stream_url
            return redirect(stream_url, code=302)

    except Exception as e:
        return f"Error: {str(e)}", 500

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
