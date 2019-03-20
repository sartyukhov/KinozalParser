from urllib.request import urlopen
from re             import findall


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

# select script working mode
class Mode:
    LOCAL = 1
    WEB   = 2

QUALITY = Quality._1080p
SORT    = Sort.Pirs
DAYS    = Days._3
#debug - LOCAL / Release - WEB
MODE    = Mode.LOCAL

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
    def getInfo(self, num=None):
        return '\n'.join(x.getInfo() for x in self.files[:num])

class Torrent:
    def __init__(self, id, name, source, quality):
        self.id      = id
        self.name    = name
        self.source  = source
        self.quality = quality
    def getInfo(self):
        return '{0:50} | {1:7} | {2:7} | {3}'\
            .format(self.name, self.id, self.quality, self.source)
    def getUrl(self):
        return 'http://kinozal.tv/details.php?id=' + self.id

def getContentFromPage(name, url):
    htmlFile = name.replace(' ', '_') + '.html'
    # download and save HTML page
    if MODE == Mode.WEB:
        with urlopen(url) as page:
            with open(htmlFile, 'wb') as outputHTML:
                outputHTML.write(page.read())
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

def getTorrentsList():
    url = "http://kinozal.tv/browse.php?s=&g=0&c=1002&v={q}&d=0&w={d}&t={s}&f=0"\
        .format(q=QUALITY, d=DAYS, s=SORT)
    
    parsed = parse(getContentFromPage('page', url))

    filesContainer = FilesContainer()
    for p in parsed:
        filesContainer.appendUnique(Torrent(p[0],p[1],p[2],p[3]))

    # sort is unnecessary now
    # filesContainer.sort()
    return filesContainer

if __name__ == "__main__":    
    with open('page.txt', 'w') as outputTXT:
        outputTXT.write(getTorrentsList().getInfo(10))