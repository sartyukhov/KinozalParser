from urllib.parse   import quote
from re             import findall
from pickle         import dump, load
from time           import time, gmtime, strftime
from enum           import Enum
from urlOpener      import getUrlContent

class TorrentsContainer:
    def __init__(self):
        self.created = time() + 10800 # UTC+3
        self.files   = []

    def appendUnique(self, item):
        if item in self:
            return False
        else:
            self.append(item)
            return True

    def append(self, item):
        self.files.append(item)



class Torrent:
    def __init__(self, id, info):
        self.id = id
        __parseInfo(info)
        print(self.id + ' ' + self.name)
        
    def __parseInfo(self, info):
        self.name = findall(r'(.*) /', info)



def parseTorrentsList(content):
    # parsing (yeah, just one string)
    fp = r'.*class="nam"><a href="/details.php\?id=(\d+).*">(.*)</a>.*>'
    return findall(fp, content)

if __name__ == "__main__":
    torrents = parseTorrentsList(getUrlContent('none', local=True))

    for t in torrents:

    print(parsed)