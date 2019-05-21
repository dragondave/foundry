import http.server
import socketserver
import queue
from threading import Thread
from time import sleep
import foundry
import requests
ready = queue.Queue()
server = None


def http_server():
    global server
    PORT = 8000
    Handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", PORT), Handler) as server:
        ready.put(1)
        print("serving at port", PORT)
        server.serve_forever()

def test_cases():
    try:
        ready.get()
        f = foundry.Foundry("http://localhost:8000/test_data/test_1.html",
            lambda root: root.xpath(".//span[@id='content']")[0])
        print (f.alloy())
    except:
        server.shutdown()
        raise

t1 = Thread(target=http_server, name="server")
t1.start()
t2 = Thread(target=test_cases, name="tests")
t2.start()
