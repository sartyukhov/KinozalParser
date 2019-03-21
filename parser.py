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
    def appendUnique(self, val):
        if val not in self:
            self.append(val)
    def append(self, val):
        self.files.append(val)
    def sort(self):
        self.files = sorted(self.files, key=lambda f: f.name)
    def getNames(self):
        return '\n'.join(x.name for x in self.files)
    def getInfo(self, num=None, separator='-', sep_size=20):
        return '\n'.join((x.getInfo() + '\n' + separator*sep_size) for x in self.files[:num])

class Torrent:
    def __init__(self, id, name, source, quality):
        self.id      = id
        self.name    = name
        self.source  = source
        self.quality = quality
        self.url     = self.__getUrl()
        self.__getMoreData()

    def __getUrl(self):
        return 'http://kinozal.tv/details.php?id=' + self.id

    def __getMoreData(self):
        parsed = parseTorrentPage(getContentFromPage('tor_page', self.url))
        self.imdbRating = parsed.get('rating', '?')
        self.size = parsed.get('size', '?')

    def getInfo(self):
        return '{n}\n{q:5} | {s:7} | [{i:7}]({u})\nIMDB {r} | Size: {si}'\
            .format(n=self.name, i=self.id, q=self.quality, s=self.source, u=self.url,
            r=self.imdbRating, si=self.size)

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
                print('UTF-8')
            except:
                pageContent = pageBuffer.decode('cp1251')
                print('cp1251')
    return pageContent

def parseTorrentsList(content):
    # parsing (yeah, just one string)
    findPattern = r'.*href="/details.php\?id=(\d+)".*"r\d">([^/]+).*/\s*(.+)\((.+)\)</a>'
    return findall(findPattern, content)

def parseTorrentPage(content):
    d = dict()
    findResult = findall(r'.*>IMDb<span class=.*>(.*)</span>', content)
    if len(findResult) > 0:
        d['rating'] = findResult[0]
    findResult = findall(r'.*>Вес<span class=".*>(.*)\(.*\)</span>', content)
    if len(findResult) > 0:
        d['size'] = findResult[0]
    return d

def getTorrentsList(readLocal=False):
    global READLOCAL
    READLOCAL = readLocal
    url = "http://kinozal.tv/browse.php?s=&g=0&c=1002&v={q}&d=0&w={d}&t={s}&f=0"\
        .format(q=QUALITY, d=DAYS, s=SORT)
    
    parsed = parseTorrentsList(getContentFromPage('page', url))

    filesContainer = FilesContainer()
    for p in parsed:
        filesContainer.appendUnique(Torrent(p[0],p[1],p[2],p[3]))

    return filesContainer

if __name__ == "__main__":
    READLOCAL = False
    print(getContentFromPage('tor_page', 'http://kinozal.tv/'))
