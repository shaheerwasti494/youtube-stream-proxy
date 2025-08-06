from flask import Flask, request, redirect
from yt_dlp import YoutubeDL
from cachetools import TTLCache

app = Flask(__name__)
cache = TTLCache(maxsize=1000, ttl=300)  # cache up to 1000 IDs for 5 minutes

@app.route('/stream')
def stream():
    vid = request.args.get('id')
    if not vid:
        return 'Missing id', 400

    # Check cache first
    if vid not in cache:
        ydl_opts = {'format': 'best[ext=mp4]/best'}
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f'https://youtu.be/{vid}', download=False)
        # Pick 720p MP4 if available, else fallback to best
        fmts = [f for f in info['formats'] if f.get('ext') == 'mp4']
        url = next((f['url'] for f in fmts if f.get('height') == 720), info['url'])
        cache[vid] = url

    return redirect(cache[vid], code=302)

if __name__ == '__main__':
    # Bind to PORT env var if Railway sets it, else default to 8000
    import os
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)
