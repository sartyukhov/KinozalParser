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
    def getUrl(self):
        return 'http://kinozal.tv/details.php?id=' + self.id
    def getInfo(self):
        return '{n}\n{q:5} | {s:7} | [{i:7}]({u})'\
            .format(n=self.name, i=self.id, q=self.quality, s=self.source, u=self.getUrl())

def getContentFromPage(name, url, readLocal):
    pathToScript = os.path.dirname(os.path.abspath(__file__))
    htmlFile = '{}{}{}.html'.format(pathToScript, SLASH, name.replace(' ', '_'))
    # download and save HTML page
    if not readLocal:
        with urlopen(url) as page:
            with open(htmlFile, 'wb') as outputHTML:
                outputHTML.write(page.read())
                print(outputHTML.name + ' created')
    # get saved HTML data to parse
    pageContent = ''
    try:
        with open(htmlFile, 'r', encoding='windows 1251') as inputHTML:
            pageContent = inputHTML.read()
    except:
        with open(htmlFile, 'r', encoding='UTF-8') as inputHTML:
            pageContent = inputHTML.read()
    return pageContent

def parse(content):
    # parsing (yeah, just one string)
    findPattern = r'.*href="/details.php\?id=(\d+)".*"r\d">([^/]+).*/\s*(.+)\((.+)\)</a>'
    return findall(findPattern, content)

def getTorrentsList(readLocal=False):
    url = "http://kinozal.tv/browse.php?s=&g=0&c=1002&v={q}&d=0&w={d}&t={s}&f=0"\
        .format(q=QUALITY, d=DAYS, s=SORT)
    
    parsed = parse(getContentFromPage('page', url, readLocal))

    filesContainer = FilesContainer()
    for p in parsed:
        filesContainer.appendUnique(Torrent(p[0],p[1],p[2],p[3]))

    # sort is unnecessary now
    # filesContainer.sort()
    return filesContainer

if __name__ == "__main__":
    pass
