import requests

BAD_TYPES = ["text/css", "text/javascript", "text/plain"]

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
    try:
        content_type = r.headers['Content-Type'].split(";")[0].strip()
    except KeyError:
        content_type = ""
    
    if content_type == "text/html":
        return None
    if content_type in BAD_TYPES:
        return None
    return r