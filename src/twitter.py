import tweepy

api: tweepy.API = None


def init(user_auth):
    global api

    auth = tweepy.OAuthHandler(user_auth['consumer_key'], user_auth['consumer_secret'])
    auth.set_access_token(user_auth['access_token'], user_auth['access_token_secret'])

    api = tweepy.API(auth)


def follow(username):
    if api is not None:
        try:
            api.create_friendship(username)
        except tweepy.error.TweepError as e:
            # print(e)
            pass


def retweet(tweet_id):
    if api is not None:
        try:
            api.retweet(tweet_id)
        except tweepy.error.TweepError:
            return


def tweet(text):
    if api is not None:
        try:
            api.update_status(text)
        except tweepy.error.TweepError:
            return
