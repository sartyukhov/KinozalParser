#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from urllib.request import urlopen
from re             import findall
from sys            import platform
import os

if platform == 'linux':
    SLASH = '/'
else:
    SLASH = '\\'

READLOCAL = True

#select quality
class Quality():
    _4K    = 7
    _1080p = 3
    _720p  = 3

#select sort
class Sort():
    Sids = 1
    Pirs = 2

#select days
class Days():
    _1 = 1
    _3 = 3

QUALITY = Quality._1080p
SORT    = Sort.Pirs
DAYS    = Days._3

class FilesContainer:
    def __init__(self):
        self.files = []
    def __getitem__(self, key):
        return self.files[key]
    def __setitem__(self, key, val):
        self.files[key] = val
    def __iter__(self):
        return iter(self.files)
    def __contains__(self, item):
        for f in self.files:
            if f.name == item.name:
                return True
        return False
    def appendUnique(self, item):
        if item in self:
            # for f in self.files:
            #     if f.name == item.name:
            #         pos = self.files.index(f)
            #         self.files.remove(f)
            return False
        else:
            self.append(item)
            return True
    def append(self, item):
        self.files.append(item)
    def sort(self):
        self.files = sorted(self.files, key=lambda f: f.name)
    def getNames(self):
        return '\n'.join(x.name for x in self.files)
    def getInfo(self, separator='-', sep_size=20):
        return '\n'.join((x.getInfo() + '\n' + separator*sep_size) for x in self.files)

class Torrent:
    def __init__(self, num, id, name, source, quality):
        self.num     = num
        self.id      = id
        self.name    = name
        self.source  = source
        self.quality = quality
        self.url     = self.__getUrl()

    def __getUrl(self):
        return 'http://kinozal.tv/details.php?id=' + self.id

    def __getMoreData(self):
        parsed = parseTorrentPage(getContentFromPage('tor_page', self.url))
        self.imdbUrl    = parsed.get('raturl', '?')
        self.imdbRating = parsed.get('rating', '?')
        self.size = parsed.get('size', '?')

    def getInfo(self):
        self.__getMoreData()
        return '{N} : {n}\n{q:5} | {s:7} | [{i:7}]({u})\n[IMDB]({ru}) {r} | Size: {si}'\
            .format(n=self.name, i=self.id, q=self.quality, s=self.source, u=self.url,
            ru=self.imdbUrl, r=self.imdbRating, si=self.size, N=(self.num + 1))

def getContentFromPage(name, url):
    pathToScript = os.path.dirname(os.path.abspath(__file__))
    htmlFile = '{}{}{}.html'.format(pathToScript, SLASH, name.replace(' ', '_'))
    # pageContent = ''
    # get saved HTML data to parse
    global READLOCAL
    if READLOCAL:
        try:
            with open(htmlFile, 'r', encoding='UTF-8') as inputHTML:
                pageContent = inputHTML.read()
        except:
            with open(htmlFile, 'r', encoding='cp1251') as inputHTML:
                pageContent = inputHTML.read()
    else: 
    # download HTML page
        with urlopen(url) as page:
            pageBuffer = page.read()
            try:
                pageContent = pageBuffer.decode('UTF-8')
                print('Page {} opened in UTF-8'.format(name))
            except:
                pageContent = pageBuffer.decode('cp1251')
                print('Page {} opened in cp1251'.format(name))
    return pageContent

def parseTorrentsList(content):
    # parsing (yeah, just one string)
    findPattern = r'.*href="/details.php\?id=(\d+)".*"r\d">([^/]+).*/\s*(.+)\((.+)\)</a>'
    return findall(findPattern, content)

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

def getTorrentsList(num=0, readLocal=False):
    global READLOCAL
    READLOCAL = readLocal
    url = "http://kinozal.tv/browse.php?s=&g=0&c=1002&v={q}&d=0&w={d}&t={s}&f=0"\
        .format(q=QUALITY, d=DAYS, s=SORT)
    
    torrents = parseTorrentsList(getContentFromPage('page', url))

    filesContainer = FilesContainer()
    counter = 0
    for t in torrents:
        if (filesContainer.appendUnique(Torrent(counter, t[0], t[1], t[2], t[3]))):
            counter += 1
            if counter >= num:
                break

    return filesContainer

if __name__ == "__main__":
    print(getContentFromPage('tor_page', 'http://kinozal.tv/'))
