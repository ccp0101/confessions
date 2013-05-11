from flask import Flask, render_template, request, abort
from flask.ext.pymongo import PyMongo
from db import MONGO_URI
import os
from renren import RenRen
from bson import ObjectId
import pymongo

app = Flask(__name__)
app.config["MONGO_URI"] = MONGO_URI
mongo = PyMongo(app)

if not app.debug:
    import logging
    from logging.handlers import RotatingFileHandler
    file_handler = RotatingFileHandler(
        os.path.join(os.path.dirname(os.path.realpath(__file__)),
            "web.log"))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)

def getBot():
    renren = RenRen()
    renren.login(os.environ["RENREN_USERNAME"], os.environ["RENREN_PASSWORD"])
    renren.switchAccount("2020816463")
    return renren

@app.route('/')
def index():
    page = int(request.args.get('page', 1))
    limit = 50
    confessions = mongo.db.confessions.find().sort("received_at", pymongo.DESCENDING
                                            ).limit(limit).skip((page - 1) * limit)
    count = mongo.db.confessions.count()
    pager = {}
    if count > page * limit:
        pager["newer"] = "/?page=%i" % page + 1
    if page > 1:
        pager["older"] = "/?page=%i" % page - 1
    return render_template("list.html", confessions=confessions, pager=pager)

@app.route('/publish', methods=['POST'])
def publish():
    id, message = ObjectId(request.form["id"]), request.form["message"]
    confession = mongo.db.confessions.find_one({"_id": id})
    renren = getBot()
    confession["status"] = renren.addStatus(601726248, message)
    confession["published"] = True
    mongo.db.confessions.save(confession)
    return ""

@app.route('/undo', methods=['POST'])
def undo():
    confession = mongo.db.confessions.find_one({"_id": ObjectId(request.form["id"])})
    if confession["published"]:
        status_id = int(confession["status"]["updateStatusId"])
        renren = getBot()
        deletion = renren.deleteStatus(601726248, status_id)
        confession.setdefault("deletions", [])
        confession["deletions"].append({"status": confession["status"], "deletion": deletion})
        confession["status"] = None
        confession["published"] = False
        mongo.db.confessions.save(confession)
        return ""
    else:
        abort(403)

app.run("0.0.0.0", 8012, threaded=True)
