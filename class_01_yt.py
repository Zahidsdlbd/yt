from flask import Flask, request, redirect, abort, Response
import requests
import re
import logging # Import logging for better error handling and debugging
# Removed: import urllib.parse # No longer needed without playlist URL parsing

# Configure logging to see messages in the console
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

def get_yt_hls(video_id):
    """
    Attempts to retrieve the HLS manifest URL for a given YouTube video ID or channel handle.
    WARNING: This method relies on scraping YouTube's HTML, which is highly unstable
    and prone to breaking due to YouTube's frequent website changes and anti-scraping measures.
    It is not a reliable or officially supported way to get YouTube HLS streams.
    """
    if video_id.startswith('@'):
        # This URL structure for live streams via channel handles is speculative
        # and may not consistently provide an HLS manifest.
        url = f"https://www.youtube.com/{video_id}/live"
        logging.info(f"Attempting to fetch live stream URL for channel handle: {video_id} from {url}")
    else:
        # This URL structure for regular video IDs is also prone to changes in YouTube's embedding.
        url = f"https://www.youtube.com/watch?v={video_id}"
        logging.info(f"Attempting to fetch video URL for ID: {video_id} from {url}")

    headers = {
        # Using a more complete User-Agent string can sometimes help avoid immediate blocks.
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Referer": "https://www.youtube.com/", # Essential for YouTube requests
        "Origin": "https://www.youtube.com"   # Essential for YouTube requests
    }

    try:
        # Make the HTTP GET request to YouTube
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)

        # Search for the HLS manifest URL in the response text.
        # This regex depends heavily on YouTube's internal JSON structure within the HTML,
        # which is subject to change without notice.
        match = re.search(r'"hlsManifestUrl":"([^"]+)"', r.text)
        if match:
            hls_url = match.group(1).replace('\\u0026', '&') # Decode escaped ampersands
            logging.info(f"Successfully found HLS URL for {video_id}: {hls_url}")
            return hls_url
        else:
            logging.warning(f"HLS manifest URL pattern not found in YouTube response for {video_id}.")
            # Log a snippet of the response content for debugging purposes if the pattern isn't found.
            # Be careful not to log too much sensitive data in production.
            logging.debug(f"Partial response content for {video_id}:\n{r.text[:1000]}...")
    except requests.exceptions.RequestException as e:
        # Catch specific request-related errors (e.g., network issues, timeouts, bad HTTP status)
        logging.error(f"Request failed for video_id {video_id}: {e}")
    except Exception as e:
        # Catch any other unexpected errors
        logging.error(f"An unexpected error occurred while processing video_id {video_id}: {e}")
    
    return None # Return None if HLS URL could not be found or an error occurred


@app.route("/<video_id>/index.m3u8")
def yt_redirect(video_id):
    """
    Flask route to redirect to the YouTube HLS manifest URL for a single video.
    Access this route like: http://127.0.0.1:5000/dQw4w9WgXcQ/index.m3u8
    (replace dQw4w9WgXcQ with your desired YouTube video ID or channel handle)
    """
    hls_url = get_yt_hls(video_id)
    if hls_url:
        logging.info(f"Redirecting request for {video_id} to {hls_url}")
        return redirect(hls_url)
    else:
        logging.error(f"Failed to retrieve HLS URL for video_id {video_id}. Returning 503.")
        # Provide a more informative error message to the client
        return abort(503, description="Service Unavailable: Could not retrieve YouTube HLS stream.")


# Removed: @app.route("/playlist.m3u8") and the generate_playlist function


if __name__ == "__main__":
    # When deploying to a production environment, debug=True should be avoided.
    # Gunicorn will handle the server aspect, so app.run() is not needed directly.
    # This block will only execute if the script is run directly (e.g., for local testing).
    logging.info("Starting Flask application locally in debug mode on port 5000.")
    app.run(debug=True, port=5000)
