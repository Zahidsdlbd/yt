from flask import Flask , request , redirect , abort
import requests
import re

app = Flask(__name__)

def get_yt_hls(video_id):
    if video_id.startswith('@'):
        url = f"https://www.youtube.com/{video_id}/live"
    else:
        url = f"https://www.youtube.com/watch?v={video_id}"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://www.youtube.com/",
        "Origin": "https://www.youtube.com"
    }
    try:
        r = requests.get(url, headers=headers, timeout=10)
        match = re.search(r'"hlsManifestUrl":"([^"]+)"', r.text)
        if match:
            return match.group(1).replace('\\u0026', '&')
    except:
        pass
    return None


@app.route("/<video_id>/index.m3u8")
def yt_redirect(video_id):
    hls_url = get_yt_hls(video_id)
    if hls_url:
        return redirect(hls_url)
    return abort(503)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
