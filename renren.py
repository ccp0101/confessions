#-*-coding:utf-8-*-

# 人人各种接口

import requests
import json
import re
import random
# from pyquery import PyQuery
import os
from BeautifulSoup import BeautifulSoup
import pickle

# 分段加密
CHUNK_SIZE = 30

# RSA加密
def enctypt(e, m, c):
    return pow(c, e, m)

# 加密一段
def enctyptChunk(e, m, chunk):
    chunk = map(ord, chunk)

    # 补成偶数长度
    if not len(chunk) % 2 == 0:
        chunk.append(0)

    nums = [chunk[i] + (chunk[i + 1] << 8) for i in range(0, len(chunk), 2)]

    c = sum([n << i * 16 for i, n in enumerate(nums)])

    encypted = enctypt(e, m, c)

    # 转成16进制并且去掉开头的0x
    return hex(encypted)[2:]

# 加密字符串，如果比较长，则分段加密
def encryptString(e, m, s):
    e, m = int(e, 16), int(m, 16)

    chunks = [s[:CHUNK_SIZE], s[CHUNK_SIZE:]] if len(s) > CHUNK_SIZE else [s]

    result = [enctyptChunk(e, m, chunk) for chunk in chunks]
    return ' '.join(result)[:-1]  # 去掉最后的'L'


import logging

# these two lines enable debugging at httplib level (requests->urllib3->httplib)
# you will see the REQUEST, including HEADERS and DATA, and RESPONSE with HEADERS but without DATA.
# the only thing missing will be the response.body which is not logged.
import httplib
httplib.HTTPConnection.debuglevel = 1

logging.basicConfig() # you need to initialize logging, otherwise you will not see anything from requests
logging.getLogger().setLevel(logging.DEBUG)
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True

class RenRen:
    def __init__(self, email=None, pwd=None):
        self.session = requests.Session()

        self.token = {}

        if email and pwd:
            self.login(email, pwd)

    def loginByCookie(self, cookie_path=None):
        if cookie_path is None:
            cookie_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "cookie.jar")
        with open(cookie_path) as fp:
            cookie_dict = pickle.load(fp)
        self.session.cookies = requests.utils.cookiejar_from_dict(cookie_dict)
        self.getToken()

    def saveCookie(self, cookie_path=None):
        if cookie_path is None:
            cookie_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "cookie.jar")
        with open(cookie_path, 'w') as fp:
            cookie_dict = requests.utils.dict_from_cookiejar(self.session.cookies)
            pickle.dump(cookie_dict, fp)

    def login(self, email, pwd):
        key = self.getEncryptKey()

        if self.getShowCaptcha(email) == 1:
            fn = 'icode.%s.jpg' % os.getpid()
            self.getICode(fn)
            print "Please input the code in file '%s':" % fn
            icode = raw_input().strip()
            os.remove(fn)
        else:
            icode = ''

        data = {
            'email': email,
            'origURL': 'http://www.renren.com/home',
            'icode': icode,
            'domain': 'renren.com',
            'key_id': 1,
            'captcha_type': 'web_login',
            'password': pwd,
#            'password': encryptString(key['e'], key['n'], pwd) if key['isEncrypt'] else pwd,
#            'rkey': key['rkey'],
            'autoLogin': "true"
        }
        print "login data: %s" % data
        url = 'http://www.renren.com/ajaxLogin/login?1=1&uniqueTimestamp=%f' % random.random()
        r = self.post(url, data)
        result = r.json()
        if result['code']:
            print 'login successfully'
            self.email = email
            r = self.get(result['homeUrl'])
            self.getToken(r.text)
        else:
            print 'login error', r.text

    def getICode(self, fn):
        r = self.get("http://icode.renren.com/getcode.do?t=web_login&rnd=%s" % random.random())
        if r.status_code == 200 and r.raw.headers['content-type'] == 'image/jpeg':
            with open(fn, 'wb') as f:
                for chunk in r.iter_content():
                    f.write(chunk)
        else:
            print "get icode failure"

    def getShowCaptcha(self, email=None):
        r = self.post('http://www.renren.com/ajax/ShowCaptcha', data={'email': email})
        return r.json()

    def getEncryptKey(self):
        r = requests.get('http://login.renren.com/ajax/getEncryptKey')
        return r.json()

    def getToken(self, html=''):
        p = re.compile("get_check:'(.*)',get_check_x:'(.*)',env")

        if not html:
            r = self.get('http://www.renren.com')
            html = r.text

        result = p.search(html)
        self.token = {
            'requestToken': result.group(1),
            '_rtk': result.group(2)
        }

    def request(self, url, method, data={}):
        if data:
            data.update(self.token)

        if method == 'get':
            return self.session.get(url, data=data)
        elif method == 'post':
            return self.session.post(url, data=data)

    def get(self, url, data={}):
        return self.request(url, 'get', data)

    def post(self, url, data={}):
        return self.request(url, 'post', data)

    def getUserInfo(self):
        r = self.get('http://notify.renren.com/wpi/getonlinecount.do')
        return r.json()

    def getNotifications(self):
        url = 'http://notify.renren.com/rmessage/get?getbybigtype=1&bigtype=1&limit=50&begin=0&view=17'
        r = self.get(url)
        try:
            result = json.loads(r.text, strict=False)
        except Exception, e:
            print 'error', e
            raise e
            result = []
        return result

    def removeNotification(self, notify_id, uid=""):
        # http://notify.renren.com/remove.notify?nl=42776992424&uid=601726248
        url = 'http://notify.renren.com/remove.notify?nl=' + str(notify_id)
        if uid:
            url += "&uid=" + uid
        return self.get(url).text

    def removeNotificationMultiple(self, notify_ids, uid, type):
        joined = "-".join([str(x) for x in notify_ids])
        url = "http://notify.renren.com/rmessage/process?nl=%s&uid=%s&type=%s" % (
            joined, str(uid), str(type))
        print url
        return self.get(url).text

    def getDoings(self, uid, page=0):
        url = 'http://status.renren.com/GetSomeomeDoingList.do?userId=%s&curpage=%d' % (str(uid), page)
        r = self.get(url)
        return r.json().get('doingArray', [])

    def getDoingById(self, owner_id, doing_id):
        doings = self.getDoings(owner_id)
        doing = filter(lambda doing: doing['id'] == doing_id, doings)
        return doing[0] if doing else None

    def getDoingComments(self, owner_id, doing_id):
        url = 'http://status.renren.com/feedcommentretrieve.do'
        r = self.post(url, {
            'doingId': doing_id,
            'source': doing_id,
            'owner': owner_id,
            't': 3
        })

        return r.json()['replyList']

    def getCommentById(self, owner_id, doing_id, comment_id):
        comments = self.getDoingComments(owner_id, doing_id)
        comment = filter(lambda comment: comment['id'] == int(comment_id), comments)
        return comment[0] if comment else None

    def addComment(self, data):
        return {
            'status': self.addStatusComment,
            'album' : self.addAlbumComment,
            'photo' : self.addPhotoComment,
            'blog'  : self.addBlogComment,
            'share' : self.addShareComment,
            'gossip': self.addGossip
        }[data['type']](data)

    def sendComment(self, url, payloads):
        for i in range(10):  # try 3 times
            r = self.post(url, payloads)
            if r.status_code != 500:
                break
            time.sleep(2)
        r.raise_for_status()
        try:
            return r.json()
        except:
            print r.text.encode("utf8")
            return { 'code': 0 }

    # 评论状态
    def addStatusComment(self, data):
        url = 'http://status.renren.com/feedcommentreply.do'

        payloads = {
            't': 3,
            'rpLayer': 0,
            'source': data['source_id'],
            'owner': data['owner_id'],
            'c': data['message']
        }

        if data.get('reply_id', None):
            payloads.update({
                'rpLayer': 1,
                'replyTo': data['author_id'],
                'replyName': data['author_name'],
                'secondaryReplyId': data['reply_id'],
                'c': '回复%s：%s' % (data['author_name'].encode('utf-8'), data['message'])
            })

        return self.sendComment(url, payloads)

    # 回复留言
    def addGossip(self, data):
        url = 'http://gossip.renren.com/gossip.do'
        
        payloads = {
            'id': data['owner_id'], 
            'only_to_me': 1,
            'mode': 'conversation',
            'cc': data['author_id'],
            'body': data['message'],
            'ref':'http://gossip.renren.com/getgossiplist.do'
        }

        return self.sendComment(url, payloads)

    # 回复分享
    def addShareComment(self, data):
        url = 'http://share.renren.com/share/addComment.do'

        if data.get('reply_id', None):
            body = '回复%s：%s' % (data['author_name'].encode('utf-8'), data['message']),
        else:
            body = data['message']
        
        payloads = {
            'comment': body,
            'shareId' : data['source_id'],
            'shareOwner': data['owner_id'],
            'replyToCommentId': data.get('reply_id', 0),
            'repetNo' : data.get('author_id', 0)
        }

        return self.sendComment(url, payloads)

    # 回复日志
    def addBlogComment(self, data):
        url = 'http://blog.renren.com/PostComment.do'
        
        payloads = {
            'body': '回复%s：%s' % (data['author_name'].encode('utf-8'), data['message']),
            'feedComment': 'true',
            'guestName': '小黄鸡', 
            'id' : data['source_id'],
            'only_to_me': 0,
            'owner': data['owner_id'],
            'replyCommentId': data['reply_id'],
            'to': data['author_id']
        }

        return self.sendComment(url, payloads)

    # 回复相册
    def addAlbumComment(self, data):
        url = 'http://photo.renren.com/photo/%d/album-%d/comment' % (data['owner_id'], data['source_id'])
        
        payloads = {
            'id': data['source_id'],
            'only_to_me' : 'false',
            'body': '回复%s：%s' % (data['author_name'].encode('utf-8'), data['message']),
            'feedComment' : 'true', 
            'owner' : data['owner_id'],
            'replyCommentId' : data['reply_id'],
            'to' : data['author_id']
        }

        return self.sendComment(url, payloads)

    def addPhotoComment(self, data):
        url = 'http://photo.renren.com/photo/%d/photo-%d/comment' % (data['owner_id'], data['source_id'])

        if 'author_name' in data:
            body = '回复%s：%s' % (data['author_name'].encode('utf-8'), data['message']),
        else:
            body = data['message']
        
        payloads = {
            'guestName': '小黄鸡',
            'feedComment' : 'true',
            'body': body,
            'owner' : data['owner_id'],
            'realWhisper':'false',
            'replyCommentId' : data.get('reply_id', 0),
            'to' : data.get('author_id', 0)
        }

        return self.sendComment(url, payloads)

    # 访问某人页面
    def visit(self, uid):
        self.get('http://www.renren.com/' + str(uid) + '/profile')

    # 根据关键词搜索最新状态(全站)
    def searchStatus(self, keyword, max_length=20):
        url = 'http://browse.renren.com/s/status?offset=0&sort=1&range=0&q=%s&l=%d' % (keyword, max_length)
        r = self.session.get(url, timeout=5)
        status_elements = PyQuery(r.text)('.list_status .status_content')
        id_pattern  = re.compile("forwardDoing\('(\d+)','(\d+)'\)")
        results = []
        for index, _ in enumerate(status_elements):
            status_element = status_elements.eq(index)

            # 跳过转发的
            if status_element('.status_root_msg'):
                continue

            status_element = status_element('.status_content_footer')
            status_time = status_element('span').text()
            m = id_pattern.search(status_element('.share_status').attr('onclick'))
            status_id, user_id = m.groups()
            results.append( (int(user_id), int(status_id), status_time) )
        return results

    def switchAccount(self, account_id):
        payloads = {
            'origUrl': 'http://www.renren.com/home',
            'destId': account_id,
        }
        r = self.post('http://www.renren.com/switchAccount', data=payloads)
        r.raise_for_status()
        self.getToken(self.get("http://www.renren.com/home").text)
        return True

    def addStatus(self, author_id, status):
        url = "http://shell.renren.com/" + str(author_id) + "/status"
        payloads = {
            "content": status,
            "hostid": author_id,
            "channel": "renren"
        }
        r = self.post(url, data=payloads)
        r.raise_for_status()
        return r.json()

    def deleteStatus(self, author_id, status_id):
        url = "http://page.renren.com/" + str(author_id) + "/fdoing/" + str(status_id) + "/delete"
        r = self.post(url)
        r.raise_for_status()
        return r.json()

    def getGossips(self, from_user):
        url = "http://gossip.renren.com/getconversation.do"
        payloads = {
            "guest": from_user,
            "curpage":0,
            "destpage":0,
            "hostBeginId": "",
            "hostEndId": "",
            "guestBeginId": "",
            "guestEndId": "",
            "page": "",
            "id": from_user,
            "resource":0,
            "search":0,
            "boundary":0,
            "gossipCount":0,
        }
        r = self.post(url, data=payloads)
        r.raise_for_status()
        return r.json()["array"]

    def getHTMLGossipsUsers(self):
        url = "http://notify.renren.com/rmessage/rmessage-apply.html?view=16&page=1&bigtype=1"
        r = self.get(url)
        r.raise_for_status()
        return re.findall(r"getgossiplist\.do\?id=[0-9]{9}&f=([0-9]{9})", r.text)

    def getMailIDs(self, uid):
        url = "http://page.renren.com/%s/msg/listMsg" % (str(uid))
        r = self.get(url)
        r.raise_for_status()
        ids = re.findall(r'id="thread_([0-9]{9,11})"', r.text)
        return list(set(ids))

    def getMail(self, uid, id):
        url = "http://page.renren.com/%s/msg/read?id=%s" % (str(uid), str(id))
        r = self.get(url)
        r.raise_for_status()
        soup = BeautifulSoup(r.text)
        body = ''.join(soup.findAll('div', {"class" : "text"})[0].findAll(text=True))
        author_info = soup.findAll('div', {"class": re.compile(r".*\bauthor_info\b.*")})[0]
        author_id = re.findall(r"id=([0-9]{9})", str(author_info))[0]
        author_name = author_info.findAll("a")[0].text
        return {
            "id": id,
            "body": body,
            "author_id": author_id,
            "author_name": author_name
        }