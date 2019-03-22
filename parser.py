#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from urllib.request import urlopen
from re             import findall
from sys            import platform
from pickle         import dump, load
from time           import time
# from datetime       import datetime as date
import os

if platform == 'linux':
    SLASH = '/'
else:
    SLASH = '\\'

READLOCAL = True
SPATH = os.path.dirname(os.path.abspath(__file__))

#select file
class Content():
    Movies = 1002

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

CONTENT = Content.Movies
QUALITY = Quality._1080p
SORT    = Sort.Pirs
DAYS    = Days._3


class TorrentsContainer:
    # class variables
    dbName = '{}{}{}.db'.format(SPATH, SLASH, 'torrentsList')
    num    = 10
    dbfreshtime = 1800
    forceupdate = False

    @classmethod
    def Config(cls, num, dbfreshtime, forceupdate):
        cls.num = num
        cls.dbfreshtime = dbfreshtime
        cls.forceupdate = forceupdate

    def __init__(self):
        self.created = time()
        self.files   = []
        if self.forceupdate:
            self.update()
        else:
            self.load()

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

    def load(self):
        try:
            with open(self.dbName, 'rb') as db:
                old = load(db)
                print('[L]: Database loaded')
        except Exception as e:
            print('[L]: Database load failed')
            print('[E]: ' + str(e))
            self.update()
        else:
            if (self.created - old.created) > self.dbfreshtime:
                print('[L]: Database is too old')
                self.update()
            else:
                self.created = old.created
                self.files   = old.files
                print('[L]: Database was used successfully')
    
    def dump(self):
        try:
            with open(self.dbName, 'wb') as db:
                dump(self, db)
                print('[L]: Database on disk updated')
        except Exception as e:
            print('[L]: Database on disk update failed') 
            print('[E]: ' + str(e))

    def update(self):
        url = "http://kinozal.tv/browse.php?s=&g=0&c={c}&v={q}&d=0&w={d}&t={s}&f=0"\
            .format(c=CONTENT, q=QUALITY, d=DAYS, s=SORT)

        torrentsList = parseTorrentsList(getContentFromPage('page', url))

        counter = 0
        for t in torrentsList:
            if (self.appendUnique(Torrent(counter, t[0], t[1], t[2], t[3]))):
                counter += 1
                if counter >= self.num:
                    break
        self.dump()

    def appendUnique(self, item):
        if item in self:
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

    def getInfo(self, separator='~', sep_size=15):
        t = 'Новые раздачи на Kinozal.tv\n\n'
        t += ('\n'.join((x.getInfo() + '\n' + separator*sep_size) for x in self.files))
        self.dump()
        return t

class Torrent:
    def __init__(self, num, id, name, source, quality):
        self.num     = num
        self.id      = id
        self.name    = name
        self.source  = source
        self.quality = quality
        self.url     = self.__getUrl()
        self.moreDataExists = False

    def __getUrl(self):
        return 'http://kinozal.tv/details.php?id=' + self.id

    def __getMoreData(self):
        if (not self.moreDataExists):
            parsed = parseTorrentPage(getContentFromPage('tor_page', self.url))
            self.imdbUrl    = parsed.get('raturl', '?')
            self.imdbRating = parsed.get('rating', '?')
            self.size = parsed.get('size', '?')
            self.moreDataExists = True

    def getInfo(self):
        self.__getMoreData()
        return '{N} : {n}\n{q:5} | {s:7} | [{i:7}]({u})\n[IMDB]({ru}) {r} | Size: {si}'\
            .format(n=self.name, i=self.id, q=self.quality, s=self.source, u=self.url,
            ru=self.imdbUrl, r=self.imdbRating, si=self.size, N=(self.num + 1))

def getContentFromPage(name, url):
    htmlFile = '{}{}{}.html'.format(SPATH, SLASH, name.replace(' ', '_'))
    # get saved HTML data to parse
    global READLOCAL
    if READLOCAL:
        try:
            with open(htmlFile, 'r', encoding='UTF-8') as inputHTML:
                pageContent = inputHTML.read()
                print('[L]: URL page {} opened in UTF-8 (local)'.format(name))
        except:
            with open(htmlFile, 'r', encoding='cp1251') as inputHTML:
                pageContent = inputHTML.read()
                print('[L]: URL page {} opened in cp1251 (local)'.format(name))
    else: 
    # download HTML page
        with urlopen(url) as page:
            pageBuffer = page.read()
            try:
                pageContent = pageBuffer.decode('UTF-8')
                print('[L]: URL page {} opened in UTF-8'.format(name))
            except:
                pageContent = pageBuffer.decode('cp1251')
                print('[L]: URL page {} opened in cp1251'.format(name))
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

def getTorrentsList(num, dbfreshtime, forceupdate, readLocal=False):
    # set debug/working mode
    global READLOCAL
    READLOCAL = readLocal

    TorrentsContainer.Config(num, dbfreshtime, forceupdate)

    torrentsContainer = TorrentsContainer()

    return torrentsContainer

if __name__ == "__main__":
    pass
    # print(getContentFromPage('tor_page', 'http://kinozal.tv/'))
