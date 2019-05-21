Foundry
    .url: source url
    .domains: domains of interest
    .melt(): get bytes of url resource into raw_content
    .raw_content: bytes of url resoure
    .centrifuge_callback: function to delete lxml bits
    .centrifuge(): get relevant bits of HTML, return bytes
    .centrifuged: bytes of useful HTML
    .alloy

class Foundry(object):
    def __init__(self, url, centrifuge_callback):
        self.url = url
        self.domains = DOMAINS
        self.domains.append(urlparse(self.url).netloc)
        self.melt() # self.content
        assert type(self.raw_content) == bytes
        self.centrifuge(centrifuge_callback)
        assert type(self.centrifuged) == bytes

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
        new_root = lxml.html.fromstring('<html><head><meta charset="UTF-8"><link rel="stylesheet" type="text/css" href="styles.css" preserve=true></head><body></body></html>') # PRESERVE
        body, = new_root.xpath("//body")
        body.append(main)
        absolve(body, self.url)
        self.centrifuged = lxml.html.tostring(new_root)

    def alloy(self):
        root = lxml.html.fromstring(self.centrifuged)
        handled = {} # {url:filename}
        for attr in URL_ATTRS:
            tags = root.xpath("//*[@{}]".format(attr))
            for tag in tags:
                attribute_value = tag.attrib[attr]
                # ignore certain tags
                if PRESERVE in tag.attrib:
                    continue
                for starter in ["#", "mailto:", "javascript:"]:
                    if attribute_value.startswith(starter):
                        continue

                # MODIFICATION: Tag is now absolute
                tag.attrib[attr] = urljoin(self.url, tag.attrib[attr])


                if "youtube.com/" in tag.attrib or "youtu.be/" in tag.attrib:
                    filename = handle_youtube(tag)  # placeholder, do something with file
                    continue

                # TODO: handle links which are indirectly resources with a callback here.

                if attribute_value in handled:
                    # If already handled this URL, rewrite and don't download
                    tag.attrib[attr] = handled[attribute_value]
                    continue

                response = get_resource(attribute_value)
                if response is None:
                    if tag.tag == "a":
                        globalise(tag) # give it a pretty globe if it's a link we're not crawling.
                    continue # bail out either way.

                # We now have a resource (specifically: request response) we must save.
                content_type = response.headers['Content-Type'].split(";")[0].strip()
                extension = mimetypes.guess_extension(content_type) or "" # .mp3
                filename = hashlib.sha1(attribute_value.encode('utf-8')).hexdigest() + extension


        self.alloyed = lxml.html.tostring(root)
        return self.alloyed


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

    print (f.alloy())

