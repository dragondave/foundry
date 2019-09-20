# why is is called foundry?
# because HoT MetaL.

# *groan*
import requests
import lxml.html
import shutil
import hashlib
import os

from urllib.parse import urljoin, urlparse
from pathlib import Path
import shutil
from .lxml_tools import global_hyperlink, absolve, handle_youtube, globalise
from .bits import get_resource, nice_ext
from ricecooker.utils.downloader import read as Downloader
from ricecooker.utils.zip import create_predictable_zip
from ricecooker.classes.nodes import HTML5AppNode
from ricecooker.classes.files import HTMLZipFile

DEBUG = False
def debug(*s):
    if DEBUG:
        print(*s)

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TEMP_FOUNDRY_ZIP = Path("__foundry/")
URL_ATTRS = ["src", "href"]
PRESERVE = "preserve"
DOMAINS = []
PACKAGE_PATH = Path(os.path.dirname(os.path.realpath(__file__)))
CSS_FILENAME = "styles.css"
CSS_PATH = PACKAGE_PATH / CSS_FILENAME

copyright_holder = None

class Foundry(object):
    def __init__(self, url, centrifuge_callback=None, metadata=None, owndomain=True):
        self.metadata = metadata or {}
        self.files = {}
        self.url = url
        self.domains = DOMAINS
        if owndomain:
            self.domains.append(urlparse(self.url).netloc)
        self.melt() # self.content
        assert type(self.raw_content) == bytes
        self.centrifuge(centrifuge_callback)
        assert type(self.centrifuged) == bytes
        self.alloy()
        self.cast()

    def get_license(self):
        return "Public Domain"  # TODO

    def melt(self):
        """
        Return the binary data found at `url`.
        Sets self.raw_content
        Other versions might need to use cookies for login
        Or might use ricecooker.utils.downloader.read
        Or load from disk

        This version is just a placeholder.

        Input: self.url
        Output: html bytes
        """
        # return a binary representation of the URL
        self.raw_content = requests.get(self.url).content


    def centrifuge(self, callback=None):
        """
        Select only the relevant parts of the HTML.

        Tasks:
        * Ensure CSS / encoding correct (is inline)
        * Ensure URLs fully referenced (lxml_tools.absolve)

        Option: replace entirely with conversion to/from Markdown
        Option: Additional cleaning of the HTML to remove other junk we don't care about
                e.g. CSS, gubbins attributes, misc. span/div

        Input: html bytes
        Output: html bytes
        """

        assert callback, "callback is required"
        root = lxml.html.fromstring(self.raw_content)
        main = callback(root)
        new_root = lxml.html.fromstring('<html><head><meta charset="UTF-8"><link rel="stylesheet" type="text/css" href="{}" preserve=true></head><body></body></html>'.format(CSS_PATH))
        body, = new_root.xpath("//body")
        body.append(main)
        absolve(body, self.url)
        self.centrifuged = lxml.html.tostring(new_root)

    def alloy(self):
        """Modify the relevant HTML to create a structure suitable for becoming a HTML5App"""
        root = lxml.html.fromstring(self.centrifuged)
        debug("alloying")

        for attr in URL_ATTRS:
            tags = root.xpath("//*[@{}]".format(attr))
            for tag in tags:
                bail = False
                attribute_value = tag.attrib[attr]
                debug("TAG ATTR:", attribute_value)

                # ignore certain tags
                if PRESERVE in tag.attrib:
                    continue
                for starter in ["#", "mailto:", "javascript:"]:
                    if attribute_value.startswith(starter):
                        debug("STARTER", starter)
                        bail = True
                if bail: continue

                # MODIFICATION: Tag is now absolute
                tag.attrib[attr] = urljoin(self.url, tag.attrib[attr])
                absolute_value = tag.attrib[attr]
                del attribute_value  # don't use relative URL again
                tag_domain = urlparse(absolute_value).netloc # www.youtube.com

                # handle offsite links: youtube, others
                if "youtube.com" in tag_domain or "youtu.be" in tag_domain:
                    filename = handle_youtube(tag)  # placeholder, do something with file
                    continue

                if tag_domain not in self.domains and tag.tag=="a":
                    globalise(tag)
                    continue

                # TODO: handle links which are indirectly resources with a callback here.
                # TODO: correctly handle HTML resources ... somehow!

                if absolute_value in self.files:
                    # If already handled this URL, rewrite and don't download
                    tag.attrib[attr] = self.files[absolute_value]
                    continue

                response = get_resource(absolute_value)
                if response is None:
                    debug("Bad link", absolute_value)
                    continue # bail out either way.

                # We now have a resource (specifically: request response) we must save.
                extension = nice_ext(response)
                filename = hashlib.sha1(absolute_value.encode('utf-8')).hexdigest() + extension
                self.files[absolute_value] = filename
                tag.attrib[attr] = filename
        self.alloyed = lxml.html.tostring(root)
        return self.alloyed

    def title(self):
        "a stab at getting the title -- probably to be overwritten"
        root = lxml.html.fromstring(self.centrifuged)
        try:
            h1, = root.xpath("//h1")
        except ValueError:
            return "Placeholder"
        return h1.text_content().strip()

    def thumb(self):
        "a stab at getting the thumbnail -- probably to be overwritten"
        root = lxml.html.fromstring(self.centrifuged)
        root.make_links_absolute(self.url)
        srcs = root.xpath("//img/@src")
        try:
            src = srcs[0]
        except IndexError:
            return None
        return src

    def cast(self):
        """
        Create a zip file containing:
            * index.html = self.alloyed
            * files from self.files (urls)
            * static files from disk [i.e. css]
        """
        assert "__" in str(TEMP_FOUNDRY_ZIP)
        try:
            shutil.rmtree(TEMP_FOUNDRY_ZIP)
        except FileNotFoundError:
            pass
        os.mkdir(TEMP_FOUNDRY_ZIP)
        with open(TEMP_FOUNDRY_ZIP / "index.html", "wb") as f:
            f.write(self.alloyed)
        shutil.copyfile(CSS_PATH, TEMP_FOUNDRY_ZIP / CSS_FILENAME)
        for url, filename in self.files.items():
            data = Downloader(url)
            with open(TEMP_FOUNDRY_ZIP / filename, "wb") as f:
                f.write(data)
        self.zipname = create_predictable_zip(str(TEMP_FOUNDRY_ZIP))

    def node(self):
        return HTML5AppNode(
                source_id=self.url,
                title=self.title(),
                license=self.get_license(),
                copyright_holder=copyright_holder,
                thumbnail=self.thumb(),
                files = [HTMLZipFile(self.zipname)],
                **self.metadata
               )

def wiki_xpath(root):
    content, = root.xpath("//div[@id='content']")
    subtitle, = content.xpath(".//div[@id='siteSub']")
    subtitle.getparent().remove(subtitle)
    return content

def mathplanet_xpath(root):
    content, = root.xpath("//article[@id='article']")
    return content

if __name__ == "__main__":
    f = Foundry("https://www.mathplanet.com/education/pre-algebra/graphing-and-functions/graphing-linear-inequalities",
                mathplanet_xpath)

    print (f.alloyed)

