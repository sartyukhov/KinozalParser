from urllib.parse   import quote, urlparse, urlunparse
from re             import findall, search, sub
from pickle         import dump, load
from time           import time, gmtime, strftime
from enum           import Enum
from urlOpener      import getUrlContent

class TorrentsContainer:
    def __init__(self, group):
        self.created = time() + 10800 # UTC+3
        self.files   = []
        self.group   = group

    def __iter__(self):
        return iter(self.files)
        
    def __contains__(self, item):
        for f in self.files:
            if f.name == item.name:
                return True
        return False

    def appendUnique(self, item):
        if item in self:
            return False
        else:
            self.append(item)
            return True

    def append(self, item):
        item.serachSelf(self.group)
        self.files.append(item)

    def sort(self):
        self.files = sorted(self.files, key=lambda f: f.name)



class Torrent:
    def __init__(self, id, info):
        self.id = id
        self.__parseInfo(info)
        
    def __parseInfo(self, info):
        info = sub(' / ', '/', info)
        self.name = search(r'[^/]*', info).group()
        self.year = search(r'[0-9]{4}(-[0-9]{4})?', info).group()

    def serachSelf(self, group):
        surl = 'http://kinozal.tv/browse.php?s={s}&g=0&c={c}&v=0&d={d}&w=0&t=3&f=0'.format(
            s=quote(self.name),
            c=group,
            d=self.year
        )
        selfs = parseTorrentsList(getUrlContent(surl))
        print(selfs)


def parseTorrentsList(content):
    # parsing (yeah, just one string)
    fp = r'.*class="nam"><a href="/details.php\?id=(\d+).*">(.*)</a>.*>'
    return findall(fp, content)

def parseTorrentPage(content):
    d = dict()
    findResult = findall(r'.*href="(.*)" target=.*>IMDb<span class=.*>(.*)</span>', content)
    if len(findResult) > 0:
        d['raturl'] = findResult[0][0]
        d['rating'] = findResult[0][1]
    findResult = findall(r'.*>Вес<span class=".*>(.*)\(.*\)</span>', content)
    if len(findResult) > 0:
        d['size'] = findResult[0]
    return d

def updateDB():
    url = 'http://kinozal.tv/browse.php?s=&g=0&c=1002&v=0&d=0&w=0&t=2&f=0&page=0'

    moviesContainer = TorrentsContainer('1002')

    torrents = parseTorrentsList(getUrlContent(url))
    for t in torrents:
        moviesContainer.appendUnique(Torrent(t[0], t[1]))

    




if __name__ == "__main__":
    # url = 'http://kinozal.tv/browse.php?s=&g=0&c=1002&v=0&d=0&w=0&t=2&f=0&page=0'
    # print(parseTorrentsList(getUrlContent(url)))
    updateDB()