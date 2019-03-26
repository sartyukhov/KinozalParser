from urllib.parse   import quote, urlparse, urlunparse
from re             import findall, search, sub
from pickle         import dump, load
from time           import time, gmtime, strftime
from urlOpener      import getUrlContent

#select file
class Content():
    TV_SHOWS = '1001'
    MOVIES   = '1002'
    CARTOONS = '1003'

#select quality
class Quality():
    _4K    = '7'
    _1080P = '3'
    _720P  = '3'

#select sort
class Sort():
    SIDS = '1'
    PIRS = '2'
    SIZE = '3'

#select days
class Days():
    ANY = '0'
    _1  = '1'
    _3  = '3'

class TorrentsContainer:
    baseUrl = 'http://kinozal.tv/browse.php?'

    @classmethod
    def load(cls, content):
        dumpName = content + '.db'
        try:
            with open(dumpName, 'rb') as db:
                old = load(db)
                print('[L]: {} database loaded'.format(dumpName))
                return old
        except Exception as e:
            print('[L]: {} database load failed'.format(dumpName))
            print('[E]: ' + str(e))

    def __init__(self, content, sort=Sort.PIRS, num=100, dump=True):
        self.created = time() + 10800 # UTC+3
        self.content = content
        self.files   = []
        #update container with content
        url = self.baseUrl + 's=&g=0&c={c}&v=0&d=0&w=0&t={t}&f=0&page=0'.format(
            c=content,
            t=sort
        )
        torrents = parseTorrentsList(getUrlContent(url, name='page'))
        for t in torrents:
            self.appendUnique(Torrent(t[0], t[1], content))
            if len(self) >= num:
                break
        if dump:
            self.dump()

    def __iter__(self):
        return iter(self.files)

    def __len__(self):
        return len(self.files)

    def __contains__(self, item):
        for f in self.files:
            if f.name == item.name:
                return True
        return False

    def append(self, item):
        item.downloadMoreInfo()
        item.serachMirrors()
        self.files.append(item)

    def appendUnique(self, item):
        if item in self:
            return False
        else:
            self.append(item)
            return True

    def dump(self):
        dumpName = self.content + '.db'
        try:
            with open(dumpName, 'wb') as db:
                dump(self, db)
                print('[L]: {} database on disk updated'.format(dumpName))
        except Exception as e:
            print('[L]: {} database on disk update failed'.format(dumpName))
            print('[E]: ' + str(e))

    def getListOfFiles(self, num):
        t = ''
        counter = 0
        for f in self.files:
            counter += 1
            t += '{N}: {n}\n[{rn}: {r}]({ru})\n'.format(
                N=counter,
                n=f.name,
                rn=f.ratsrc,
                ru=f.raturl,
                r=f.rating
            )
            if len(f.mirrors) > 0:
                m = f.mirrors[0]
                t += 'Best: [{q} {s}Gb {k}/10]({u})\n'.format(
                    s=m['size'],
                    q=m['quality'],
                    k=m['kRating'],
                    u=m['url']
                )
            if counter >= num:
                break
            t += '~' * 15 + '\n'
        t += strftime('\n\nUpd: %H:%M (%d/%m/%y) (UTC+3)', gmtime(self.created))
        return t

    def sort(self):
        self.files = sorted(self.files, key=lambda f: f.name)

class Torrent:
    baseUrl = 'http://kinozal.tv/details.php?id='
    def __init__(self, id, info, content):
        self.id = id
        self.content = content
        self.mirrors = []
        self.__parseInfo(info)

    def __parseInfo(self, info):
        info = sub(' / ', '/', info)
        self.name = search(r'[^/]*', info).group()
        self.year = search(r'[0-9]{4}(-[0-9]{4})?', info).group()

    def downloadMoreInfo(self):
        turl = self.baseUrl + self.id
        parsed = parseTorrentPage(getUrlContent(turl, name='tor_page'), rating=True)
        self.ratsrc = parsed.get('ratsrc', '?')
        self.raturl = parsed.get('raturl', '?')
        self.rating = parsed.get('rating', '?')

    def serachMirrors(self, sort=Sort.SIZE):
        surl = 'http://kinozal.tv/browse.php?s={s}&g=0&c={c}&v=0&d={d}&w=0&t={t}&f=0'.format(
            s=quote(self.name + ' ' + self.year),
            c=self.content,
            d=0,# year in name
            t=sort
        )
        print(surl)
        mirrors = parseTorrentsList(getUrlContent(surl, name='mirrors_page'))
        for m in mirrors:
            turl = self.baseUrl + m[0]
            parsed = parseTorrentPage(
                getUrlContent(turl, name='tor_page'),
                sizes=True,
                kRatings=True,
                qualitys=True
            )
            parsed['url'] = turl
            self.mirrors.append(parsed)
            print('{} : {} | {} | {}'.format(
                self.name,
                parsed['size'],
                parsed['quality'],
                parsed['kRating']
            ))

def parseTorrentsList(content):
    fp = r'.*class="nam"><a href=".*/details.php\?id=(\d+).*">(.*)</a>.*>'
    return findall(fp, content)

def parseTorrentPage(content, rating=False, sizes=False, kRatings=False, qualitys=False):
    d = dict()

    if rating:
        for db in ('IMDb', 'Кинопоиск'):
            pattern = r'.*href="(.*)" target=.*>{}<span class=.*>(.*)</span>.*'.format(db)
            findResult = findall(pattern, content)
            if len(findResult) > 0:
                d['ratsrc'] = db
                d['raturl'] = findResult[0][0]
                d['rating'] = findResult[0][1]
                break
            else:
                d['ratsrc'] = '?'
                d['raturl'] = '?'
                d['rating'] = '?'

    if sizes:
        findResult = findall(r'.*>Вес<span class=".*>.*\((.*)\)</span>.*', content)
        if len(findResult) > 0:
            d['size'] = str(round(((int(sub(',', '', findResult[0]))/1024)/1024)/1024, 2))
        else:
            d['size'] = '?'

    if kRatings:
        findResult = findall(r'.*<span itemprop="ratingValue">([^<]*).*', content)
        if len(findResult) > 0:
            d['kRating'] = findResult[0]
        else:
            d['kRating'] = '?'

    if qualitys:
        findResult = findall(r'.*<b>Качество:</b>\s?([^<]*).*', content)
        if len(findResult) > 0:
            d['quality'] = findResult[0]
        else:
            d['quality'] = '?'

    return d

def updateDB(num):
    # result saves on disk
    TorrentsContainer(Content.MOVIES, num=num)

def readDB(num):
    # result saves on disk
    return TorrentsContainer.load(Content.MOVIES).getListOfFiles(num=num)

if __name__ == "__main__":
    updateDB(20)
    print(readDB(20))