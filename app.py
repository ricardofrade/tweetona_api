from flask import Flask

from api.modules import JSONEncoder
from api.modules.celery import make_celery
from api.modules.mongo import make_mongo
from api.modules.twitter import make_twitter

app = Flask(__name__)
app.config.from_object('config')
app.json_encoder = JSONEncoder

mongo = make_mongo(app)
celery = make_celery(app)
twitter = make_twitter(app)

from api.routes import *

# need to run the worker:
# celery -A app.celery worker --loglevel=info

if __name__ == '__main__':
    app.run()
