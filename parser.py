#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# libs includes
from urllib.parse               import quote
from re                         import findall
from pickle                     import dump, load
from time                       import time, gmtime, strftime
from sys                        import platform
from os.path                    import dirname, abspath
from threading                  import Thread
from html                       import unescape
# project includes
from logger                     import logger
from dbHandler                  import contentDB, urlDB
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
    _any = '0'
    _1  = '1'
    _3  = '3'
    _yesterday = '2'
    _week      = '4'
    _month     = '5'

    @classmethod
    def toText(cls, days, case=False):
        if days == cls._1:
            return '1 день'
        elif days == cls._3:
            return '3 дня'
        elif days == cls._yesterday:
            return 'вчера'
        elif days == cls._week:
            return ('неделя' if not case else 'неделю')
        elif days == cls._month:
            return 'месяц'
        elif days == cls._any:
            return 'всё время'

class TorrentsContainer:
    ''' Collects torrents inside (array-like)
    '''
    MAX_PAGES = 5
    searchUrl = 'http://kinozal.tv/browse.php?'

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

    def __init__(self, content, days, sort):
        self.created = time() + 10800 # UTC+3
        self.content = content
        self.sort    = sort
        self.days    = days
        self.files   = []

    def update(self, num=20, dump=True):
        #update container
        for page in range(self.MAX_PAGES):
            log.debug('Parsing page ' + str(page))

            url = self.searchUrl + 's=&g=0&c={c}&v=0&d=0&w={w}&t={t}&f=0&page={p}'.format(
                c=self.content,
                t=self.sort,
                w=self.days,
                p=str(page)
            )
            for t in parseTorrentsList(getUrlData(url, name='page')):
                self.appendUnique(Torrent(self.content, t))
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
        t = '{}\n{} за {}\n\n'.format(
            contentDB.cid2Rname(self.content),
            Sort.toText(self.sort).capitalize(),
            Days.toText(self.days, case=True)
        )
        counter = 0
        for f in self.files:
            counter += 1
            if f.raturl_s:
                ratingMD = ' | [{}: {}]({})'.format(f.ratsrc, f.rating, f.raturl_s)
            else:
                ratingMD = ''
            t += '{N}: {name} / ({year})\n[Link]({selfurl}){rating}\n'.format(
                N       = counter,
                name    = f.name,
                year    = f.year,
                selfurl = f.selfUrl_s,
                rating  = ratingMD
            )
            if f.topUrl_s:
                t += '[Best: {qual} {size}]({url})\n'.format(
                    qual = f.topQuality,
                    size = f.topSize,
                    url  = f.topUrl_s
                )
            t += '[Other mirrors]({u})\n'.format(u=f.mirrorsUrl_s)
            if counter >= num:
                break
            t += '~' * 15 + '\n'
        if counter == 0:
            t += 'Подборка пуста, попробуйте изменить фильтры.\n'
        t += strftime('\nUpd: %H:%M (%d/%m/%y) (UTC+3)\n', gmtime(self.created))
        return unescape(t)

    def sort(self):
        self.files = sorted(self.files, key=lambda f: f.name)

class Torrent:
    ''' One torrent page's data
    '''
    baseUrl = 'http://kinozal.tv/details.php?id='
    def __init__(self, content, args):
        self.content      = content
        self.id           = args[0]
        self.name         = args[1]
        self.ruName       = findall(r'([^/]*)', self.name)[0]
        self.year         = args[2]
        self.quality      = args[3]
        self.size         = args[4]
        self.sids         = args[5]
        self.pirs         = args[6]
        self.uploaded     = args[7]
        self.selfUrl      = self.baseUrl + self.id
        self.selfUrl_s    = self.selfUrl

        self.ratsrc       = ''
        self.raturl       = ''
        self.rating       = ''
        self.raturl_s     = ''

        self.topUrl       = ''
        self.topUrl_s     = ''
        self.topQuality   = ''
        self.topSize      = ''
        self.mirrorsUrl   = ''
        self.mirrorsUrl_s = ''

    def downloadMoreInfo(self):
        # get rating 
        parsed = parseTorrentPage(getUrlData(self.baseUrl + self.id, name='tor_page'))
        self.ratsrc = parsed.get('ratsrc', '')
        self.raturl = parsed.get('raturl', '')
        self.rating = parsed.get('rating', '')
        # get best quelity
        self.mirrorsUrl =  TorrentsContainer.searchUrl
        self.mirrorsUrl += 's={s}&g=0&c={c}&v=0&d=0&w=0&t={t}&f=0'\
            .format(
                s=quote(self.ruName + ' ' + self.year),
                c=self.content,
                t=Sort.SIZE
            )
        mirrors = parseTorrentsList(getUrlData(self.mirrorsUrl, name='mirrors_page'))
        if len(mirrors) > 0:
            topMirror       = mirrors[0]
            self.topUrl     = self.baseUrl + topMirror[0]
            self.topQuality = topMirror[3]
            self.topSize    = topMirror[4]
        # get shorter urls
        self.selfUrl_s    = urlDB.getShortUrl(self.selfUrl)
        self.raturl_s     = urlDB.getShortUrl(self.raturl)     if self.raturl     else ''
        self.topUrl_s     = urlDB.getShortUrl(self.topUrl)     if self.topUrl     else ''
        self.mirrorsUrl_s = urlDB.getShortUrl(self.mirrorsUrl) if self.mirrorsUrl else ''

def searchTorrents(name):
    ''' Search request
    '''
    url = TorrentsContainer.searchUrl
    url += 's={s}&g=0&c=0&v=0&d=0&w=0&t={t}&f=0'\
        .format(
            s=quote(name),
            t=Sort.NEW
        )
    s_res = parseTorrentsList(getUrlData(url, name='mirrors_page'))
    t = 'Результат поиска по:\n{}\n\n'.format(name)
    counter = 0
    for each in s_res:
        counter += 1
        tor = Torrent(0, each)
        t += '{c}. {n}[{qs}]({url})\n'.format(
            c=counter, 
            n=tor.ruName,
            qs=tor.quality + ' ' + tor.size,
            url=tor.selfUrl
        )

    if counter == 0:
        t += 'Ничего не найдено'

    return t

def parseTorrentsList(data):
    ''' Parse html page (search result) and find all torrents (+ data)
        Result tuple:
            [0] : id
            [1] : name
            [2] : year
            [3] : quality
            [4] : size
            [5] : sids
            [6] : pirs
            [7] : uploaded
    '''
    data = data.replace('\'', '\"')
    fp =  r'<td class="nam"><a href=.*/details.php\?id=(\d+).*">(.*) / ([1-2]{1}[0-9]{3})'
    fp += r'.* / (.*)</a>.*\n'
    fp += r'<td class="s">(.*)</td>\n'
    fp += r'<td class="sl_s">(\d*)</td>\n'
    fp += r'<td class="sl_p">(\d*)</td>\n'
    fp += r'<td class="s">(.*)</td>\n'
    return findall(fp, data)

def parseTorrentPage(data):
    ''' Parse html page (torrent page) and find ratings
        Result dict:
            d[ratsrc] : database source (IMDB or Kinozal)
            d[raturl] : rating url
            d[rating] : rating value (0:10)
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
        for days in (Days._1, Days._3, Days._week, Days._month, Days._any):
            w1 = Thread(target=TorrentsContainer(cid, days, Sort.PIRS).update)
            w2 = Thread(target=TorrentsContainer(cid, days, Sort.SIDS).update)
            w3 = Thread(target=TorrentsContainer(cid, days, Sort.NEW).update)
            w1.start()
            w2.start()
            w3.start()
            w1.join()
            w2.join()
            w3.join()

    seconds = '{:.1f}'.format(time() - t1)
    log.debug('Full data base update made in {} seconds'.format(seconds))
    return seconds

if __name__ == "__main__":
    updateDB()