from flask import Flask, redirect, abort
import requests
import re
import logging
import os

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def resolve_live_video_id(channel_handle):
    """
    Resolves the actual live video ID from a YouTube channel's live page (e.g. @JamunaTVbd/live).
    """
    url = f"https://www.youtube.com/{channel_handle}/live"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Referer": "https://www.youtube.com/",
        "Origin": "https://www.youtube.com"
    }

    try:
        logging.info(f"Resolving video ID for channel handle: {channel_handle}")
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        match = re.search(r'"videoId":"([^"]+)"', r.text)
        if match:
            video_id = match.group(1)
            logging.info(f"Resolved video ID: {video_id}")
            return video_id
        else:
            logging.warning(f"videoId not found in response for {channel_handle}")
    except requests.RequestException as e:
        logging.error(f"Error resolving live video ID: {e}")
    return None


def get_yt_hls(video_id):
    """
    Retrieves the HLS (.m3u8) stream URL from a YouTube video or live channel.
    """
    if video_id.startswith('@'):
        resolved = resolve_live_video_id(video_id)
        if not resolved:
            return None
        video_id = resolved

    url = f"https://www.youtube.com/watch?v={video_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Referer": "https://www.youtube.com/",
        "Origin": "https://www.youtube.com"
    }

    try:
        logging.info(f"Fetching HLS for video ID: {video_id}")
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        match = re.search(r'"hlsManifestUrl":"([^"]+)"', r.text)
        if match:
            hls_url = match.group(1).replace('\\u0026', '&')
            logging.info(f"Found HLS URL: {hls_url}")
            return hls_url
        else:
            logging.warning(f"HLS URL not found for video ID: {video_id}")
    except requests.RequestException as e:
        logging.error(f"Error fetching video page: {e}")
    return None


@app.route("/<video_id>/index.m3u8")
def yt_redirect(video_id):
    hls_url = get_yt_hls(video_id)
    if hls_url:
        return redirect(hls_url)
    return abort(503, description="Service Unavailable: Could not retrieve YouTube HLS stream.")


# Handle favicon.ico to avoid 404 log spam
@app.route('/favicon.ico')
def favicon():
    return '', 204


# For local dev & Render compatibility
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # Render will set PORT environment variable
    logging.info(f"Starting app on port {port}")
    app.run(debug=False, host="0.0.0.0", port=port)
