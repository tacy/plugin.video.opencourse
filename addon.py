# -*- coding:utf-8 -*-
from xbmcswift2 import Plugin
from BeautifulSoup import BeautifulSoup
import urllib2, re
from ChineseKeyboard import Keyboard

plugin = Plugin()

def _http(url):
    """
    open url return beautifulsoup
    """
    try:
        req = urllib2.Request(url)
        req.add_header('User-Agent', ' Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1500.71 Safari/537.36')
        conn = urllib2.urlopen(req)
    except Exception as e:
        raise e
    resp = conn.read()
    conn.close()
    return BeautifulSoup(resp, fromEncoding='gb18030')

@plugin.route('/')
def index():
    """
    index item
    """
    item = [
        {'label': u"按课程分类", 'path': plugin.url_for('catagorys', subject='course')},
        {'label': u"按学校分类", 'path': plugin.url_for('catagorys', subject='school')},
        {'label': u"TED10", 'path': plugin.url_for('tedten', url='http://v.163.com/special/ted10collection/')},
        {'label': u"搜索", 'path': plugin.url_for('courseLists', url='search')}
        ]
    return item

@plugin.route('/catagorys/<subject>')
def catagorys(subject):
    """
    scratch catagory url, catagory by school or course or search
    """
    url = 'http://so.open.163.com/movie/listpage/listprogram1/pl2/default/default/fc/ot/default/1.html'
    soup = _http(url)
    result = soup.findAll("ul",{'class': 'contentSliderArea-list cDBlue'})
    #print result
    catagoryList = result[0].findAll('a') if subject=='course' else result[1].findAll('a')
    item = [{
        'label': menu.string,
        'path': plugin.url_for('courseLists', url=menu.get('href')),
    } for menu in catagoryList]
    return item

@plugin.route('/courseLists/<url>/')
def courseLists(url):
    """
    scratch course list
    """
    if url == 'search':
        url = 'http://so.open.163.com/movie/search/searchprogram/ot0/tacy/1.html?vs='
        kb = Keyboard('',u'请输入搜索关键字')
        kb.doModal()
        if kb.isConfirmed():
            searchStr = kb.getText()
            searchStr2 =  unicode(searchStr, 'utf-8')
            url = url + urllib2.quote(searchStr2.encode('gb18030'))
        print url
    soup = _http(url)
    courseDiv = soup.find('div', {'class': 'contentArea-tabContent on'})
    courseUl = courseDiv.find('ul', {'class': 'contentArea-resultList'})
    pageList = courseDiv.find('div', {'class': 'page'})
    courseList = courseUl.findAll('a', {'class': None})
    item = []
    rePatten = re.compile(r'href="(.*?)".*?>([^<\n].*?)<', re.DOTALL)
    for tmp in courseList:
        urllist = re.search(rePatten, str(tmp))
        if urllist:
            # print urlGroup.group(1) + urlGroup.group(2)
            item.append({
                'label': urllist.group(2),
                'path': plugin.url_for('courseInfos', url=urllist.group(1)),
            })

    rePatten = re.compile(r'href="(.*?)">(\D.*?)</a>')
    pageGroup = re.findall(rePatten, str(pageList))
    for pg in pageGroup:
        tmp = unicode(pg[1], 'utf-8')
        if tmp==u'上一页': item.insert(0, {'label': u'上一页', 'path': plugin.url_for('courseLists', url=pg[0]),})
        if tmp==u'下一页': item.append({'label': u'下一页', 'path': plugin.url_for('courseLists', url=pg[0]),})
    return item

@plugin.route('/ted10/<url>')
def tedten(url):
    """
    ted 10 collection
    Arguments:
    - `url`:
    """
    item = []
    soup = _http(url)
    rePatten = re.compile(r'class="f-cb" href="(.*?)".*?f-thide">(.*?)</p>', re.DOTALL)
    urllist = re.findall(rePatten, str(soup))
    #print urllist
    for aurl in urllist:
        # print urlGroup.group(1) + urlGroup.group(2)
        #print aurl[1]
        item.append({
            'label': aurl[1],
            'path': plugin.url_for('playTED', url=aurl[0]),
            'is_playable': True,
        })
    return item

@plugin.route('/courseInfos/<url>')
def courseInfos(url):
    """
    scratch course video url
    """
    soup = _http(url)
    courseTable = soup.find('table', id='list2')
    item = []
    print courseTable
    #rePatten = re.compile(r'\s+(\[.*\]?)\s+<a.*?>(.*?)</a>\s+.*\s+.*\s+.*\s+.*\s+.*\s+.*\s+.*\s+.*href="(.*?)"')
    rePatten = re.compile(r'(\[.*?\]).*?>(.*?)</a>.*?downbtn" href="(.*?.mp4)', re.DOTALL)
    courseGroup = re.findall(rePatten, str(courseTable))
    for menu in courseGroup:
        print menu[2]
        labstr = menu[0] + menu[1] if menu[2] != '#' else menu[0] + menu[1] + u'  (未翻译课程，无法播放)'
        item.append({
            'label': labstr,
            'path': plugin.url_for('playCourse', url=menu[2]),
            'is_playable': True,
        })
    return item

@plugin.route('/playCourse/<url>')
def playCourse(url):
    """
    play video,url 301 redirect
    Arguments:
    - `url`:course video url
    """
    resp = urllib2.urlopen(url)
    videoUrl = resp.geturl()
    print '+++++++++++++++++++++++' + videoUrl
    plugin.set_resolved_url(videoUrl)

@plugin.route('/playTED/<url>')
def playTED(url):
    """
    ted course play
    Arguments:
    - `url`:
    """
    match = re.search(r'/([\w]+/[\w]+)/(\w+).html', url)
    url2 = 'http://live.ws.126.net/movie/' + match.group(1) + '/2_' + match.group(2) + '.xml'
    #print '++++++++++++++++++++', url2
    resp = urllib2.urlopen(url2)
    match2 = re.search(r'playurl_origin.*(http://.*shd.mp4).*?(http://.*?\.srt)', resp.read())
    #print '+++++++++++++++++++++++', match2.group(1), match2.group(2)
    resp2 = urllib2.urlopen(match2.group(1))
    videourl = resp2.geturl()
    print 'videourl+++++++++++++++++++++++', videourl
    plugin.set_resolved_url(videourl,match2.group(2))

if __name__ == '__main__':
    plugin.run()
