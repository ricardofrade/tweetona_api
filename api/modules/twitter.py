from birdy.twitter import AppClient
from birdy.twitter import TwitterRateLimitError
from delorean import parse, epoch

RATE_LIMIT_REMAINING_THRESHOLD = 10  # between 0 - 1500


def make_twitter(app):
    twitter = Twitter(
        consumer_key=app.config['TWITTER_CONSUMER_KEY'],
        consumer_secret=app.config['TWITTER_CONSUMER_SECRET']
    )
    return twitter


class Twitter(object):
    """Class to collect the most recent Tweets posted by the user from the Twitter REST API.
    Utilizes the birdy AppClient. Handles client reconnection for
    connection pool disconnects. Provides automated pagination.

    Manages the statuses API rate limit with limit info from the API itself --
    no need to pace your queries, but if using beyond the rate limit, your
    queries will get delayed as needed."""

    def __init__(self, consumer_key, consumer_secret):
        self._client = None
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.rate_limit_remaining = 1
        self.rate_limit_limit = None
        self.rate_limit_reset = None
        self.twitter_date = None
        self.first_request = True

    @property
    def client(self):
        if self._client is None:
            self._client = AppClient(consumer_key=self.consumer_key, consumer_secret=self.consumer_secret)
            self._client.get_access_token()
        return self._client

    def extract_rate_limit(self, response):
        """Extract rate limit info from response/headers.

        The rate limit Twitter API request response provides bad data in the
        headers, so check the payload first and fallback to headers for other
        request types."""
        try:
            data = response.data['resources']['statuses']['/statuses/user_timeline']
            self.rate_limit_remaining = data['remaining']
            self.rate_limit_limit = data['limit']
            self.rate_limit_reset = epoch(data['reset']).datetime
        except (KeyError, TypeError):
            self.rate_limit_remaining = int(response.headers['x-rate-limit-remaining'])
            self.rate_limit_limit = int(response.headers['x-rate-limit-limit'])
            self.rate_limit_reset = epoch(int(response.headers['x-rate-limit-reset'])).datetime
        self.twitter_date = parse(response.headers['date']).datetime

    def get_rate_limit(self):
        """Send statuses rate limit info request to Twitter API."""
        response = self.client.api.application.rate_limit_status.get(resources='statuses')
        self.extract_rate_limit(response)
        return {
            'limit': self.rate_limit_limit,
            'remaining': self.rate_limit_remaining,
            'reset': self.rate_limit_reset
        }

    def wait_for_reset(self):
        """Requires header information to be current."""
        t = (self.rate_limit_reset - self.twitter_date).seconds + 1  # to grow on
        return t

    def get_user_timeline(self, **kwargs):
        """Passes kwargs to statuses.user_timeline.get of the AppClient.
        For kwargs requirements, see docs for birdy AppClient."""
        if self.first_request:
            self.get_rate_limit()
            self.first_request = False
        if self.rate_limit_remaining <= RATE_LIMIT_REMAINING_THRESHOLD:
            raise TwitterRateLimitError('reached rate limit')
        response = self.client.api.statuses.user_timeline.get(**kwargs)
        self.extract_rate_limit(response)
        return response.data

    def get_all_user_timeline(self, **kwargs):
        """Twitter only allows access to a users most recent 3200 tweets with this method."""
        new_tweets = self.get_user_timeline(**kwargs)
        if len(new_tweets) > 0:
            kwargs['max_id'] = new_tweets[-1].id - 1
            return new_tweets + self.get_all_user_timeline(**kwargs)
        return new_tweets
