import foundry
import requests
import lxml.html
from lxml_tools import GLOBE
def assert_unchanged(_id):
    xpath = ".//*[@id='{}']".format(_id)
    orig = lxml.html.tostring(original_root.xpath(xpath)[0])
    found = lxml.html.tostring(foundry_root.xpath(xpath)[0])
    assert orig == found, [orig, found]

def href(_id):
    return foundry_root.xpath(".//*[@id='{}']/@href".format(_id))[0]

def src(_id):
    return foundry_root.xpath(".//*[@id='{}']/@src".format(_id))[0]
URL = "http://localhost:8000/test_data/test_1.html"
original_root = lxml.html.fromstring(requests.get(URL).content)
f = foundry.Foundry(URL, lambda root: root.xpath(".//span[@id='content']")[0])
foundry_root = lxml.html.fromstring(f.alloy())

assert "badpdf" in original_root.xpath(".//@id")
assert "badpdf" not in foundry_root.xpath(".//@id")

assert_unchanged("preserved")
assert_unchanged("email")
assert_unchanged("javascript")
assert_unchanged("anchor")
assert GLOBE in foundry_root.xpath(".//*[@id='offsite']/text()")[0]

assert "/" not in href("pdf")
assert href("pdf") == href("pdf2")
assert "/" not in src("jpeg")
assert src("jpeg") in f.files.values()
assert href("pdf") in f.files.values()
# onsite TODO

#print (f.alloy())
#zipout = f.cast()
node = f.node()
assert node.title == "h1 title"

