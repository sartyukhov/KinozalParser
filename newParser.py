from urllib.parse   import quote, urlparse, urlunparse
from re             import findall, search, sub
from pickle         import dump, load
from time           import time, gmtime, strftime
from enum           import Enum
from urlOpener      import getUrlContent

#select file
class Content(Enum):
    TV_SHOWS = '1001'
    MOVIES   = '1002'
    CARTOONS = '1003'

#select quality
class Quality(Enum):
    _4K    = '7'
    _1080P = '3'
    _720P  = '3'

#select sort
class Sort(Enum):
    SIDS = '1'
    PIRS = '2'
    SIZE = '3'

#select days
class Days(Enum):
    ANY = '0'
    _1  = '1'
    _3  = '3'

class TorrentsContainer:
    baseUrl = 'http://kinozal.tv/browse.php?'
    def __init__(self, content, sort=Sort.PIRS, num=100):
        self.created = time() + 10800 # UTC+3
        self.content = content
        self.sort    = sort
        self.files   = []
        #update container with content
        url = self.baseUrl + 's=&g=0&c={c}&v=0&d=0&w=0&t={t}&f=0&page=0'.format(
            c=self.content,
            t=self.sort
        )        
        torrents = parseTorrentsList(getUrlContent(url, name='page'))
        for t in torrents:
            self.appendUnique(Torrent(t[0], t[1]))
            if len(self) >= num:
                break

    def __iter__(self):
        return iter(self.files)
        
    def __len__(self):
        return len(self.files)

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
        item.getMoreInfo()
        item.serachMirrors(self.content)
        self.files.append(item)

    def sort(self):
        self.files = sorted(self.files, key=lambda f: f.name)


class Torrent:
    baseUrl = 'http://kinozal.tv/details.php?id='
    def __init__(self, id, info):
        self.id = id
        self.sizes    = []
        self.kRatings = []
        self.qualitys = []
        self.__parseInfo(info)
        
    def __parseInfo(self, info):
        info = sub(' / ', '/', info)
        self.name = search(r'[^/]*', info).group()
        self.year = search(r'[0-9]{4}(-[0-9]{4})?', info).group()

    def getMoreInfo(self):
        turl = self.baseUrl + self.id
        parsed = parseTorrentPage(getUrlContent(turl, name='tor_page'), rating=True)
        self.imdbUrl    = parsed.get('raturl', '?')
        self.imdbRating = parsed.get('rating', '?')

    def serachMirrors(self, content, sort=Sort.SIZE):
        surl = 'http://kinozal.tv/browse.php?s={s}&g=0&c={c}&v=0&d={d}&w=0&t={t}&f=0'.format(
            s=quote(self.name),
            c=content,
            d=self.year,
            t=sort
        )
        mirrors = parseTorrentsList(getUrlContent(surl, name='mirrors_page'))
        for m in mirrors:
            turl = self.baseUrl + m[0]
            parsed = parseTorrentPage(
                getUrlContent(turl, name='tor_page'),
                sizes=True,
                kRatings=True,
                qualitys=True
            )
            self.sizes.append(parsed.get('size', '?'))
            self.kRatings.append(parsed.get('kRating', '?'))
            self.qualitys.append(parsed.get('quality', '?'))
        print(self.sizes)
        print(self.kRatings)
        print(self.qualitys)


def parseTorrentsList(content):
    # parsing (yeah, just one string)
    fp = r'.*class="nam"><a href=".*/details.php\?id=(\d+).*">(.*)</a>.*>'
    return findall(fp, content)

def parseTorrentPage(content, rating=False, sizes=False, kRatings=False, qualitys=False):
    d = dict()

    if rating:
        for db in ('IMDb', 'Кинопоиск'):
            pattern = r'.*href="(.*)" target=.*>{}<span class=.*>(.*)</span>.*'.format(db)
            findResult = findall(pattern, content)
            if len(findResult) > 0:
                d['raturl'] = findResult[0][0]
                d['rating'] = findResult[0][1]
                break

    if sizes:
        findResult = findall(r'.*>Вес<span class=".*>.*\((.*)\)</span>.*', content)
        if len(findResult) > 0:
            d['size'] = str(round(((int(sub(',', '', findResult[0]))/1024)/1024)/1024, 2))

    if kRatings:
        findResult = findall(r'.*<span itemprop="ratingValue">([^<]*).*', content)
        if len(findResult) > 0:
            d['kRating'] = findResult[0]

    if qualitys:
        findResult = findall(r'.*<b>Качество:</b>([^<]*).*', content)
        if len(findResult) > 0:
            d['quality'] = findResult[0]       

    return d

def updateDB():
    moviesContainer = TorrentsContainer(Content.MOVIES, num=5)

if __name__ == "__main__":
    updateDB()