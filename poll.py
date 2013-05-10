#-*-coding:utf-8-*-

"""
Copyright (c) 2012 wong2 <wonderfuly@gmail.com>
Copyright (c) 2012 hupili <hpl1989@gmail.com>

Original Author:
    Wong2 <wonderfuly@gmail.com>
Changes Statement:
    Changes made by Pili Hu <hpl1989@gmail.com> on
    Jan 10 2013:
        Support captcha.

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
'Software'), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

from renren import RenRen
import time
import pymongo
from datetime import datetime
from db import getdb
import os

db = getdb()

if __name__ == '__main__':
    renren = RenRen()
    renren.login(os.environ["RENREN_USERNAME"], os.environ["RENREN_PASSWORD"])
    renren.switchAccount("2020814145")
    info = renren.getUserInfo()

    while True:
        notifications = renren.getNotifications()
        for notification in notifications:
            print "Type:", notification["type"]
            if notification["type"] == 14:  # 私信
                if u"MIT表白墙" not in notification['from_name']:
                    notify_id = notification['notify_id']

                    message = notification["msg_context"].strip()
                    print "From: %s" % notification["from_name"]
                    print message + "\n"

                    if message.startswith(u"回复MIT表白墙:"):
                        message = message.replace(u"回复MIT表白墙:", "", 1)

                    if len(message) < 6:
                        renren.addGossip({
                            'owner_id': notification['owner'],
                            'author_id': notification['from'],
                            'message': u'"%s"太短了' % message
                            })

                    else:
                        db.confessions.insert({
                                "from_name": notification["from_name"],
                                "from": notification["from"],
                                "owner": notification['owner'],
                                "received_at": datetime.utcnow(),
                                "message": message,
                                "published": False,
                                "status": None
                            })
                        reply = (u'已经收录以下留言，审核后会发布于MIT表白墙，祝贺表白成功："%s"' % message).encode("utf8")
                        renren.addGossip({
                            'owner_id': notification['owner'],
                            'author_id': notification['from'],
                            'message': reply
                            })
                        print reply + "\n"
            renren.removeNotification(notify_id)
        time.sleep(0.2)
