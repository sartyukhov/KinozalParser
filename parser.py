#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# libs includes
from urllib.parse               import quote
from re                         import findall
from pickle                     import dump, load
from time                       import time, gmtime, strftime
from datetime                   import datetime, timedelta
from sys                        import platform
from os.path                    import dirname, abspath
from threading                  import Thread
from html                       import unescape
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
    SUBS_SEP = '~' * 15 + '\n'
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
            log.debug('{} database load failed'.format(dumpName))
            new = cls(content, days, sort)
            new.update()
            return new

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
                p=page
            )
            for t in parseTorrentsList(getUrlData(url, name='page')):
                t['content'] = self.content
                self.appendUnique(Torrent(**t))
                if len(self) >= num:
                    break
            else:
                continue
            break
        if dump:
            self.dump()

    def __iter__(self):
        return iter(self.files)

    def __len__(self):
        return len(self.files)

    def __contains__(self, item):
        for f in self.files:
            if (f.name == item.name) and (f.year == item.year):
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

    def getSubscription(self, num):
        num = int(num)
        if num > len(self):
            self.update(num)

        t = '{}\n{} за {}\n\n'.format(
            contentDB.cid2Rname(self.content),
            Sort.toText(self.sort).capitalize(),
            Days.toText(self.days, case=True)
        )
        if len(self.files) == 0:
            t += 'Подборка пуста, попробуйте изменить фильтры.\n'
        else:
            for cnt, f in enumerate(self.files, 1):
                if cnt > 1:
                    t += self.SUBS_SEP

                t += '{N}: {name} / ({year})\n[Link]({selfurl}){rating}\n'.format(
                    N       = cnt,
                    name    = f.name,
                    year    = f.year,
                    selfurl = f.selfUrl,
                    rating  = f.getRatingMD()
                )
                if f.topUrl:
                    t += '[Best: {qual} {size}]({url})\n'.format(
                        qual = f.topQuality,
                        size = f.topSize,
                        url  = f.topUrl
                    )
                t += '[Other mirrors]({u})\n'.format(u=f.mirrorsUrl)
                if cnt >= num:
                    break

        t += strftime('\nUpd: %H:%M (%d/%m/%y) (UTC+3)\n', gmtime(self.created))
        return unescape(t)

    def sort(self):
        self.files = sorted(self.files, key=lambda f: f.name)

class Torrent:
    ''' One torrent page's data
    '''
    baseUrl = 'http://kinozal.tv/details.php?id='
        
    def __init__(self, id='', content=0, name='', year='', quality='', size='', sids='', 
            pirs='', uploaded='', url=''):
        
        if url:
            self.downloadFromSelfPage()
        else:
            self.id           = id
            self.content      = content
            self.name         = name
            self.ruName       = self.name.split('/')[0]
            self.year         = year
            self.quality      = quality
            self.size         = size
            self.sids         = sids
            self.pirs         = pirs
            self.uploaded     = uploaded
            self.selfUrl      = self.baseUrl + self.id

        self.topUrl       = ''
        self.topQuality   = ''
        self.topSize      = ''
        self.mirrorsUrl   = ''

    def downloadFromSelfPage(self):
        pass

    def downloadMoreInfo(self):
        # get rating
        self.rating = parseRatings(getUrlData(self.baseUrl + self.id, name='tor_page'))
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
            self.topUrl     = self.baseUrl + topMirror.get('id', '')
            self.topQuality = topMirror.get('quality', '')
            self.topSize    = topMirror.get('size', '')

    def getRatingMD(self):
        t = ''
        for rat in self.rating:
            t += ' | [{}: {}]({})'.format(rat[0], rat[2], rat[1])

        return t

def searchTorrents(name, quantity=50, sort=Sort.NEW):
    ''' Search request
    '''
    url = TorrentsContainer.searchUrl
    url += 's={s}&g=0&c=0&v=0&d=0&w=0&t={t}&f=0'\
        .format(
            s=quote(name),
            t=sort
        )
    s_res = parseTorrentsList(getUrlData(url, name='mirrors_page'))
    t = 'Результат поиска по:\n{}\n\n'.format(name)

    if len(s_res) == 0:
        t += 'Ничего не найдено'
    else:
        for cnt, each in enumerate(s_res, 1):
            tor = Torrent(**each)
            t += '{c}. {n} ({y}) [{qs}]({url})\n'.format(
                c=cnt,
                n=tor.name,
                y=tor.year,
                qs=tor.quality + ' ' + tor.size,
                url=tor.selfUrl
            )
            if cnt >= quantity:
                break
    return unescape(t)

def parseSelfPage(data):
    ''' Parse html page (torrent page)
    '''
    data = data.replace('\'', '\"')

    fp =  r'<b>Название:</b>\s?(.+)<br>\n'
    fp += r'<b>Оригинальное название:</b>\s?(.+)<br>\n'
    fp += r'<b>Год выпуска:</b>\s?([1-2]{1}[0-9]{3})<br>\n'
    fp += r'<b>Размер:</b>\s?(.+)<br>\n'
    res = findall(fp, data)
    return {}


def parseTorrentsList(data):
    ''' Parse html page (search result) and find all torrents (+ data)
    '''
    data = data.replace('\'', '\"')
    fp =  r'<td class="nam"><a href=.*/details.php\?id=(\d+).*">(.*) / ([1-2]{1}[0-9]{3})'
    fp += r'.* / (.*)</a>.*\n'
    fp += r'<td class="s">(.*)</td>\n'
    fp += r'<td class="sl_s">(\d*)</td>\n'
    fp += r'<td class="sl_p">(\d*)</td>\n'
    fp += r'<td class="s">(.*)</td>\n'
    return [{
        'id'      :res[0],
        'name'    :res[1],
        'year'    :res[2],
        'quality' :res[3],
        'size'    :res[4],
        'sids'    :res[5],
        'pirs'    :res[6],
        'uploaded':res[7]
    } for res in findall(fp, data)]

def parseRatings(data):
    ''' Parse html page (torrent page) and find ratings
        Result list of lists:
            result[0] : database source (IMDB or Kinozal)
            result[1] : rating url
            result[2] : rating value (0:10)
    '''
    result = []

    for db in ('Кинопоиск', 'IMDb'):
        pattern = r'href="(.*)" target=.*>{}<span class=.*>(.*)</span>'.format(db)
        findResult = findall(pattern, data)
        if len(findResult) > 0:
            res = []
            res.append(db)
            res.append(findResult[0][0])
            res.append(findResult[0][1])
            result.append(res)

    return result

def parseDate(data):
    D = {'января':1, 'февраля':2, 'марта':3, 'апреля':4, 'мая':5, 'июня':6,
        'июля':7, 'августа':8, 'сентября':9, 'октября':10, 'ноября':11, 'декабря':12}
    res = ''
    for t in ('Обновлен', 'Залит'):
        res = findall(r'<li>{}<span class="floatright green n">(.+)</span></li>'.format(t), data)
        if res:
            res = res[0].lower()

            if res.find('сегодня') >= 0:
                date = datetime.now().strftime('%d %m %Y')
                res = res.replace('сегодня', date)
            elif res.find('вчера') >= 0:
                date = (datetime.now() - timedelta(days=1)).strftime('%d %m %Y')
                res = res.replace('вчера', date)

            for key, val in D.items():
                if res.find(key) >= 0:
                    res = res.replace(key, '{:02}'.format(val))
                    break
            break
    return res

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