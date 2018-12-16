from flask import Flask

from modules import JSONEncoder
from modules.celery import make_celery
from modules.mongo import make_mongo
from modules.twitter import make_twitter

app = Flask(__name__)
app.config.from_object('config')
app.json_encoder = JSONEncoder

mongo = make_mongo(app)
celery = make_celery(app)
twitter = make_twitter(app)

from modules.routes import *

if __name__ == '__main__':
    app.run()
