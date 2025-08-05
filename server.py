from flask import Flask, request, redirect
from yt_dlp import YoutubeDL
from cachetools import TTLCache

app = Flask(__name__)
cache = TTLCache(maxsize=1000, ttl=300)

@app.route("/stream")
def stream():
    video_id = request.args.get("id")
    if not video_id:
        return "Missing id parameter", 400

    if video_id in cache:
        return redirect(cache[video_id], code=302)

    try:
        ydl_opts = {"quiet": True, "skip_download": True}
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://youtu.be/{video_id}", download=False)
            formats = [f for f in info["formats"] if f.get("ext") == "mp4" and f.get("url")]
            best = max(formats, key=lambda x: x.get("height", 0))
            stream_url = best["url"]
            cache[video_id] = stream_url
            return redirect(stream_url, code=302)
    except Exception as e:
        return f"Error: {str(e)}", 500

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
