import requests
import mimetypes

BAD_TYPES = ["text/css", "text/javascript", "text/plain"]
NICE_EXT = {".mp2": ".mp3", ".jpe": ".jpg"}

def nice_ext(response):
    """Return an extension for a mimetype, e.g. .mp3"""
    content_type = response.headers['Content-Type'].split(";")[0].strip()
    ext = mimetypes.guess_extension(content_type) or ""
    if ext in NICE_EXT:
        return NICE_EXT[ext]
    return ext

def get_resource(url):
    """
    Assumes: No indirection is involved -- e.g. url is directly to the content.
    Assumes: URL is not to Youtube.

    Returns either the HTTP request response or None
    """
    try:
        r = requests.get(url, verify=False)
    except requests.exceptions.InvalidURL:
        return None
    except requests.exceptions.ConnectionError:
        return None
    try:
        content_type = r.headers['Content-Type'].split(";")[0].strip()
    except KeyError:
        content_type = ""

    if content_type == "text/html":
        return None
    if content_type in BAD_TYPES:
        return None
    return r
