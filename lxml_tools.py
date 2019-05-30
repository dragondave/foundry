from urllib.parse import urljoin
from youtube_dl import YoutubeDL
import lxml.html
PRESERVE = "preserve"      # attribute on a tag which is not to be changed
URL_TAGS = ["src", "href"] # tag attributes that might be URLs
GLOBE = u"\U0001F310"

def absolve(root, url):
    "Modifies an lxml tree to make all links absolute, except those marked with PRESERVE and local #"
    tags = []
    for attr in URL_TAGS:
        tags = root.xpath("//*[@{}]".format(attr))
        for tag in tags:
            if PRESERVE in tag.attrib:
                continue
            if tag.attrib[attr].startswith("#"):
                continue
            tag.attrib[attr] = urljoin(url, tag.attrib[attr])

def handle_youtube(tag):
    attr, = [attr for attr in URL_TAGS if 'youtu' in tag.attrib.get(attr, "")]
    url = tag.attrib[attr]
    ydl_opts = {"quiet": True}
    with YoutubeDL(ydl_opts) as ydl:
        filename = ydl.download([url])
    print (repr(filename), attr)
    tag.attrib[attr] = filename
    return filename

def globalise(tag):
    """
    Mark a tag which is known to be an offsite link with a globe symbol
    """
    GLOBE = u"\U0001F310"
    if not tag.text_content().strip(): # delink if no text content
        tag.tag = "span"
    text = tag.text or ""
    tag.text = GLOBE + " " + text

def global_hyperlink(root):
    """
    Problem: Offsite links won't resolve, and it's ugly to put full hyperlinks everywhere in the main text.
    Solution: Mark them with a globe and open them in a new window.
    Additional Problem: may be ugly for images -- so we check there's text first.
    Further Problem: Some of these links might be to PDF documents, etc: check mimetype of target first, TODO
    """
    hyper = root.xpath("//a[@href]")
    for a in hyper:
        if a.attrib['href'].startswith("#"): # local anchorlink
            continue
        if a.text.starts_with(GLOBE): # don't double globe
            continue
        if not a.text_content().strip(): # no text in link -- delink
            a.tag = "span" # TODO confirm correct
            continue
        if a.text:
            a.begin = GLOBE + " " + a.text
        else:
            a.begin = GLOBE + " "

