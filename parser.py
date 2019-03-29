#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from urllib.parse               import quote
from re                         import findall, search, sub
from pickle                     import dump, load
from time                       import time, gmtime, strftime
from urlHandler.urlOpener       import getUrlData
import logging

FORMAT =u'[%(asctime)s][%(name)s][%(levelname)s]: %(message)s'
logging.basicConfig(level=logging.DEBUG, format=FORMAT, datefmt=u'%H:%M:%S')
log = logging.getLogger('parser')

#select file
class Content():
    def __init__(self, id, name):
        self.id   = id
        self.name = name

serials     = Content('1001', 'Все сериалы')
movies      = Content('1002', 'Все фильмы')
cartoons    = Content('1003', 'Все мульты')
serials_RUS = Content('45', 'Сериал - Русский')
serials_BUR = Content('46', 'Сериал - Буржуйский')

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
    MAX_PAGES = 5
    baseUrl = 'http://kinozal.tv/browse.php?'

    @classmethod
    def load(cls, content):
        dumpName = content.id + '.db'
        try:
            with open(dumpName, 'rb') as db:
                old = load(db)
                log.debug('{} database loaded'.format(dumpName))
                return old
        except Exception as e:
            log.exception('{} database load failed'.format(dumpName))

    def __init__(self, content, num=30, sort=Sort.PIRS, dump=True):
        self.created = time() + 10800 # UTC+3
        self.content = content
        self.files   = []
        #update container 
        for page in range(self.MAX_PAGES):
            log.debug('Parsing page ' + str(page))
            url = self.baseUrl + 's=&g=0&c={c}&v=0&d=0&w=0&t={t}&f=0&page={p}'.format(
                c=content.id,
                t=sort,
                p=str(page)
            )
            for t in parseTorrentsList(getUrlData(url, name='page')):
                self.appendUnique(Torrent(content, t))
                if len(self) >= num:
                    break
            if len(self) >= num:
                break
        if dump:
            self.dump()
        log.debug('Init done in {} seconds'.format(time() + 10800 - self.created))

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
        log.debug('{} files in container'.format(len(self)))

    def appendUnique(self, item):
        if item in self:
            return False
        else:
            self.append(item)
            return True

    def dump(self):
        dumpName = self.content.id + '.db'
        try:
            with open(dumpName, 'wb') as db:
                dump(self, db)
                log.debug('{} database on disk updated'.format(dumpName))
        except Exception as e:
            log.exception('{} database on disk update failed'.format(dumpName))

    def getListOfFiles(self, num):
        t = ''
        counter = 0
        for f in self.files:
            counter += 1
            t += '{N}: {n}\n{url}'.format(
                N  = counter,
                n  = f.name,
                url= f.ratingUrl
            )
            if len(f.mirrors) > 0:
                m = f.mirrors[0]
                t += 'Best: [{q} {s}]({u})\n'.format(
                    s = m[4],
                    q = m[3],
                    u = m[8]
                )
                t += '[Other mirrors]({u})\n'.format(u=f.surl)
            if counter >= num:
                break
            t += '~' * 15 + '\n'
        t += strftime('\n\nUpd: %H:%M (%d/%m/%y) (UTC+3)', gmtime(self.created))
        return t

    def sort(self):
        self.files = sorted(self.files, key=lambda f: f.name)

class Torrent:
    baseUrl = 'http://kinozal.tv/details.php?id='
    def __init__(self, content, args):
        self.content  = content
        self.id       = args[0]
        self.name     = args[1]
        self.year     = args[2]
        self.sids     = args[5]
        self.pirs     = args[6]
        self.uploaded = args[7]
        self.mirrors  = []

    def __getRatingUrl(self):
        if self.rating != '?':
            return '[{rn}: {r}]({ru})\n'.format(
                rn = self.ratsrc,
                ru = self.raturl,
                r  = self.rating
            )
        else:
            return ''

    def downloadMoreInfo(self):
        parsed = parseTorrentPage(getUrlData(self.baseUrl + self.id, name='tor_page'))
        self.ratsrc = parsed.get('ratsrc', '?')
        self.raturl = parsed.get('raturl', '?')
        self.rating = parsed.get('rating', '?')
        self.ratingUrl = self.__getRatingUrl()

    def serachMirrors(self, sort=Sort.SIZE):
        self.surl = 'http://kinozal.tv/browse.php?s={s}&g=0&c={c}&v=0&d={d}&w=0&t={t}&f=0'.format(
            s=quote(self.name + ' ' + self.year),
            c=self.content.id,
            d=0,# year in name
            t=sort
        )
        for m in parseTorrentsList(getUrlData(self.surl, name='mirrors_page')):
            m = list(m)
            m.append(self.baseUrl + m[0])
            self.mirrors.append(m)
            log.debug('Mirror added: {} {} {}'.format(m[1], m[3], m[4]))

def parseTorrentsList(data):
    data = data.replace('\'', '\"')
    fp =  r'.*<td class="nam"><a href=.*/details.php\?id=(\d+).*">(.*) / ([0-2]{2}[0-9]{2})'
    fp += r'.* / (.*)</a>.*\n'
    fp += r'<td class="s">(.*)</td>\n'
    fp += r'<td class="sl_s">(\d*)</td>\n'
    fp += r'<td class="sl_p">(\d*)</td>\n'
    fp += r'<td class="s">(.*)</td>\n'
    return findall(fp, data)

def parseTorrentPage(data):
    d = dict()

    for db in ('IMDb', 'Кинопоиск'):
        pattern = r'.*href="(.*)" target=.*>{}<span class=.*>(.*)</span>.*'.format(db)
        findResult = findall(pattern, data)
        if len(findResult) > 0:
            d['ratsrc'] = db
            d['raturl'] = findResult[0][0]
            d['rating'] = findResult[0][1]
            break
        else:
            d['ratsrc'] = '?'
            d['raturl'] = '?'
            d['rating'] = '?'

    return d

def updateDB():
    # result saves on disk
    TorrentsContainer(movies)

def readDB(num):
    # result saves on disk
    return TorrentsContainer.load(movies).getListOfFiles(num=num)

if __name__ == "__main__":
    pass
    print(movies)