#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# libs includes
from urllib.parse               import quote
from re                         import findall
from pickle                     import dump, load, dumps
from time                       import time, gmtime, strftime
from sys                        import platform
from os.path                    import dirname, abspath
# project includes
from logger                     import logger
from dbHandler                  import contentDB
from urlHandler.urlOpener       import getUrlData

log = logger.getLogger('parser')

if platform == 'linux':
    SLASH = '/'
else:
    SLASH = '\\'

SPATH = dirname(abspath(__file__))

class Sort():
    ''' Select how to sort content
    '''
    NEW  = '0'
    SIDS = '1'
    PIRS = '2'
    SIZE = '3'

    @classmethod
    def toText(cls, sort):
        if sort == cls.NEW:
            return 'по новизне'
        elif sort == cls.SIDS:
            return 'по сидам'
        elif sort == cls.PIRS:
            return 'по пирам'
        elif sort == cls.SIZE:
            return 'по размеру'
            
class Days():
    ''' Select freshness of data
    '''
    ANY = '0'
    _1  = '1'
    _3  = '3'
    _yesterday = '2'
    _week      = '4'
    _month     = '5'

    @classmethod
    def toText(cls, days):
        if days == cls._1:
            return '1 день'
        elif days == cls._3:
            return '3 дня'
        elif days == cls._yesterday:
            return 'вчера'
        elif days == cls._week:
            return 'неделя'
        elif days == cls._month:
            return 'месяц'
        elif days == cls.ANY:
            return 'любое'

class TorrentsContainer:
    ''' Collects torrents inside (array-like)
    '''
    MAX_PAGES = 5
    baseUrl = 'http://kinozal.tv/browse.php?'

    @classmethod
    def getDumpName(cls, content, days, sort):
        return '{}{}_c{}_d{}_s{}.db'.format(SPATH, SLASH, content, days, sort)

    @classmethod
    def load(cls, content, days, sort):
        dumpName = cls.getDumpName(content, days, sort)
        try:
            with open(dumpName, 'rb') as db:
                old = load(db)
                log.debug('{} database loaded'.format(dumpName))
                return old
        except:
            log.exception('{} database load failed'.format(dumpName))

    def __init__(self, content, days, sort, num=20, dump=True):
        self.created = time() + 10800 # UTC+3
        self.content = content
        self.sort    = sort
        self.days    = days
        self.files   = []
        #update container 
        for page in range(self.MAX_PAGES):
            log.debug('Parsing page ' + str(page))
            url = self.baseUrl + 's=&g=0&c={c}&v=0&d=0&w={w}&t={t}&f=0&page={p}'.format(
                c=content,
                t=sort,
                w=days,
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
        item.searchMirrors()
        self.files.append(item)
        log.debug('{} files in container'.format(len(self)))

    def appendUnique(self, item):
        if item in self:
            return False
        else:
            self.append(item)
            return True

    def dump(self):
        dumpName = self.getDumpName(self.content, self.days, self.sort)
        try:
            with open(dumpName, 'wb') as db:
                dump(self, db)
                log.debug('{} database on disk updated'.format(dumpName))
        except:
            log.exception('{} database on disk update failed'.format(dumpName))

    def getListOfFiles(self, num):
        t = '{}\n\n'.format(contentDB.cid2Rname(self.content))
        counter = 0
        for f in self.files:
            counter += 1
            t += '{N}: {name}\n[Link]({selfurl}){rating}\n'.format(
                N       = counter,
                name    = f.name,
                rating  = f.ratingUrl,
                selfurl = f.selfUrl
            )
            if len(f.mirrors) > 0:
                m = f.mirrors[0]
                t += '[Best: {qual} {size}]({url})\n'.format(
                    qual = m[3],
                    size = m[4],
                    url  = m[8]
                )
            t += '[Other mirrors]({u})\n'.format(u=f.surl)
            if counter >= num:
                break
            t += '~' * 15 + '\n'
        t += strftime('\nUpd: %H:%M (%d/%m/%y) (UTC+3)\n', gmtime(self.created))
        return t

    def sort(self):
        self.files = sorted(self.files, key=lambda f: f.name)

class Torrent:
    ''' One torrent page's data
    '''
    baseUrl = 'http://kinozal.tv/details.php?id='
    def __init__(self, content, args):
        self.content  = content
        self.id       = args[0]
        self.name     = args[1]
        self.year     = args[2]
        self.sids     = args[5]
        self.pirs     = args[6]
        self.uploaded = args[7]
        self.selfUrl  = self.baseUrl + self.id
        self.mirrors  = []

    def __getRatingUrl(self):
        if self.rating != '?':
            return ' | [{src}: {rat}]({url})'.format(
                src = self.ratsrc,
                rat = self.rating,
                url = self.raturl
            )
        else:
            return ''

    def downloadMoreInfo(self):
        parsed = parseTorrentPage(getUrlData(self.baseUrl + self.id, name='tor_page'))
        self.ratsrc = parsed.get('ratsrc', '?')
        self.raturl = parsed.get('raturl', '?')
        self.rating = parsed.get('rating', '?')
        self.ratingUrl = self.__getRatingUrl()

    def searchMirrors(self, sort=Sort.SIZE):
        self.surl = 'http://kinozal.tv/browse.php?s={s}&g=0&c={c}&v=0&d={d}&w=0&t={t}&f=0'.format(
            s=quote(self.name + ' ' + self.year),
            c=self.content,
            d=0,# year in name
            t=sort
        )
        for m in parseTorrentsList(getUrlData(self.surl, name='mirrors_page')):
            m = list(m)
            m.append(self.baseUrl + m[0])
            self.mirrors.append(m)
            log.debug('Mirror added: {} {} {}'.format(m[1], m[3], m[4]))

def parseTorrentsList(data):
    ''' Parse html page (search result) and find all torrents (+ data)
    '''
    data = data.replace('\'', '\"')
    fp =  r'<td class="nam"><a href=.*/details.php\?id=(\d+).*">(.*) / ([0-2]{2}[0-9]{2})'
    fp += r'.* / (.*)</a>.*\n'
    fp += r'<td class="s">(.*)</td>\n'
    fp += r'<td class="sl_s">(\d*)</td>\n'
    fp += r'<td class="sl_p">(\d*)</td>\n'
    fp += r'<td class="s">(.*)</td>\n'
    return findall(fp, data)

def parseTorrentPage(data):
    ''' Parse html page (torrent page) and find ratings
    '''
    d = dict()

    for db in ('IMDb', 'Кинопоиск'):
        pattern = r'href="(.*)" target=.*>{}<span class=.*>(.*)</span>'.format(db)
        findResult = findall(pattern, data)
        if len(findResult) > 0:
            d['ratsrc'] = db
            d['raturl'] = findResult[0][0]
            d['rating'] = findResult[0][1]
            break

    return d

def updateDB():
    ''' Update cids in content data base and saves result on disk
    '''
    t1 = time()

    for cid in contentDB.getCidList():
        for days in (Days._1, Days._3, Days._week):
            for sort in (Sort.NEW, Sort.SIDS, Sort.PIRS):
                TorrentsContainer(cid, days, sort)

    log.debug('Full data base update made in {:.1f} seconds'.format(time() - t1))

if __name__ == "__main__":
    updateDB()