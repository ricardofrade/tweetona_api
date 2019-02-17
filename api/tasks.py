from birdy.twitter import TwitterRateLimitError

from app import celery, twitter, app
from .modules.mongo import build_request, make_mongo


@celery.task(bind=True)
def fetch_user_timeline(self, screen_name, since_id):
    print('task id: {}, screen_name: {}, requesting...'.format(self.request.id, screen_name))
    try:
        if since_id == -1:
            tweets = twitter.get_all_user_timeline(screen_name=screen_name, count=200)
        else:
            tweets = twitter.get_all_user_timeline(screen_name=screen_name, count=200, since_id=since_id)
        if len(tweets) > 0:
            mongo = make_mongo(app)
            requests = [build_request(t) for t in tweets]
            result = mongo.db.tweets.bulk_write(requests)
            print('task id: {}, screen_name: {}, tweets upserted: {}'.format(
                self.request.id, screen_name, result.upserted_count))
        else:
            print('task id: {}, screen_name: {}, tweets upserted: {}'.format(self.request.id, screen_name, 0))
    except TwitterRateLimitError as exc:
        print('task id: {}, exception: {}'.format(self.request.id, exc))
        twitter.get_rate_limit()
        self.retry(countdown=twitter.wait_for_reset(), exc=exc)
    except Exception as exc:
        print('task id: {}, exception: {}'.format(self.request.id, exc))
