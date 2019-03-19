from urllib.request import *
from re             import *


#select quality
class Quality():
    _4K    = '4K'
    _1080p = '1080p'
    _720p  = '720p'
    url = {
        _4K    : 7,
        _1080p : 3,
        _720p  : 3
    }

#select quality
class Source():
    BDRip  = 'BDRip'
    Web_DL = 'WEB-DL'

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
SOURCE  = Source.BDRip
SORT    = Sort.Pirs
DAYS    = Days._3
#debug - LOCAL / Release - WEB
MODE    = Mode.WEB

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
    def getInfo(self):
        return '\n'.join(x.getInfo() for x in self.files)

class Torrent:
    def __init__(self, id, name):
        self.id   = id
        self.name = name
    def getInfo(self):
        return '{0:50} {1}'.format(self.name, self.id)
    def getUrl(self):
        return 'http://kinozal.tv/details.php?id=' + self.id

def parse():
    htmlFile = 'page.html'
    # download and save HTML page
    if MODE == Mode.WEB:
        url = "http://kinozal.tv/browse.php?s=&g=0&c=1002&v={q}&d=0&w={d}&t={s}&f=0"\
            .format(q=Quality.url[QUALITY], d=DAYS, s=SORT)
        with urlopen(url) as page:
            with open(htmlFile, 'wb') as outputHTML:
                outputHTML.write(page.read())
    # get saved HTML data to parse
    try:
        with open(htmlFile, 'r', encoding='windows 1251') as inputHTML:
            pageContent = inputHTML.read()
    except:
        with open(htmlFile, 'r', encoding='UTF-8') as inputHTML:
            pageContent = inputHTML.read()
    # parsing (yeah, just one string)
    findPattern = r'href.*id=(\d+)".*"r\d">([^/]+).*{s}.*{q}'.format(s=SOURCE, q=QUALITY)
    return findall(findPattern, pageContent)

def main():
    parsed = parse()
    filesContainer = FilesContainer()

    for p in parsed:
        filesContainer.appendUnique(Torrent(p[0],p[1]))

    # sort is unnecessary now
    # filesContainer.sort()

    with open('page.txt', 'w') as outputTXT:
        outputTXT.write(filesContainer.getInfo())


if __name__ == "__main__":
    main()