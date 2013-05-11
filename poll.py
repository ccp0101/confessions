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
    # info = renren.getUserInfo()
    cachedGossips = []

    def handleGossips(gossips):
        for gossip in gossips:
            if db.gossips.find({"id": gossip["id"]}).count() == 0:
                if str(gossip["guestId"]) == str(from_user):
                    message = gossip["filterOriginalBody"]
                    if message.startswith(u"回复MIT表白墙:"):
                        message = message.replace(u"回复MIT表白墙:", "", 1)

                    conf = {
                            "from_name": gossip["guestName"],
                            "from": gossip["guestId"],
                            "owner": gossip["owner"],
                            "received_at": datetime.utcnow(),
                            "message": message,
                            "published": False,
                            "status": None
                        }
                    db.confessions.insert(conf)
                    print "Added Confession: ", conf

                    reply = u'已经收录以下留言，审核后会发布于MIT表白墙，祝贺表白成功："%s"' % message
                    print "addGossip:", renren.addGossip({
                        'owner_id': gossip["owner"],
                        'author_id': gossip["guestId"],
                        'message': reply
                        })
                    print "Reply: ", (reply + u"\n").encode("utf8")
                db.gossips.insert(gossip)
            cachedGossips.append(gossip["id"])

    for i in range(200):
        notifications = renren.getNotifications()

        notif_gossips = filter(lambda n: n["type"] == 14, notifications)
        non_gossips = filter(lambda n: n["type"] != 14, notifications)

        print "Non-Gossips:"
        print non_gossips, "\n"

        from_users = list(set(map(lambda n: n["from"], notif_gossips)))
        print "Unique from_users: ", from_users

        for from_user in from_users:
            gossips = renren.getGossips(from_user)
            gossips = filter(lambda g: g["id"] not in cachedGossips, gossips)
            print "getGossips(%s):" % from_user, gossips, "\n"
            handleGossips(gossips)

            notifs = filter(lambda n: n["from"] == from_user, notif_gossips)
            notif_ids = map(lambda n: n["notify_id"], notifs)
            renren.removeNotificationMultiple(notif_ids, "601726248", 14)
            for n in notifs:
                renren.removeNotification(n["notify_id"])
    
        from_users = renren.getHTMLGossipsUsers()
        print "getHTMLGossipsUsers: ", from_users
        for from_user in from_users:
            gossips = renren.getGossips(from_user)
            gossips = filter(lambda g: g["id"] not in cachedGossips, gossips)
            print "getHTMLGossipsUsers(%s):" % from_user, gossips, "\n"
            handleGossips(gossips)

        for mail_id in renren.getMailIDs("601726248"):
            if db.mails.find({"id": mail_id}).count() == 0:
                mail = renren.getMail("601726248", mail_id)
                conf = {
                        "from_name": mail["author_name"],
                        "from": mail["author_id"],
                        "owner": "601726248",
                        "received_at": datetime.utcnow(),
                        "message": mail["body"],
                        "published": False,
                        "status": None
                    }
                db.confessions.insert(conf)
                print "Added Confession: ", conf
                db.mails.insert(mail)
        time.sleep(30.0)