import pymongo
import os

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://127.0.0.1/MIT-Love-Confessions")

def getdb():
    conn = pymongo.Connection(MONGO_URI)
    return conn["MIT-Love-Confessions"]
