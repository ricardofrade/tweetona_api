from flask_pymongo import PyMongo
from pymongo import DESCENDING, ReplaceOne


def make_mongo(app, set_indexes=True):
    mongo = PyMongo(app)
    if set_indexes:
        make_indexes(mongo)
    return mongo


def make_indexes(mongo):
    # mongo.db.tweets.drop_indexes()
    if 'user_index' not in mongo.db.tweets.index_information():
        mongo.db.tweets.create_index([('id', DESCENDING), ('user.screen_name', DESCENDING)], name='user_index')


def build_request(obj):
    _ID = '_id'  # mongo primary key
    tweet = obj.copy()
    tweet[_ID] = obj.id
    return ReplaceOne({_ID: tweet[_ID]}, tweet, upsert=True)
