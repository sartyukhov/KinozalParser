from urllib.request import urlopen
from sys            import platform
from os.path        import dirname, abspath

if platform == 'linux':
    SLASH = '/'
else:
    SLASH = '\\'

SPATH = dirname(abspath(__file__))

def getUrlContent(url, local=False, name='page'):
    # get saved HTML data to parse
    if local:
        htmlFile = '{}{}{}.html'.format(SPATH, SLASH, name.replace(' ', '_'))
        try:
            with open(htmlFile, 'r', encoding='UTF-8') as inputHTML:
                content = inputHTML.read()
                print('[L]: URL page {} opened in UTF-8 (local)'.format(name))
        except:
            with open(htmlFile, 'r', encoding='cp1251') as inputHTML:
                content = inputHTML.read()
                print('[L]: URL page {} opened in cp1251 (local)'.format(name))
    else: 
    # download HTML page
        with urlopen(url) as page:
            pageBuffer = page.read()
            try:
                content = pageBuffer.decode('UTF-8')
                print('[L]: URL page {} opened in UTF-8'.format(name))
            except:
                content = pageBuffer.decode('cp1251')
                print('[L]: URL page {} opened in cp1251'.format(name))
    return content