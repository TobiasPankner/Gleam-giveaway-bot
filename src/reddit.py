import itertools
import re

import praw

reddit = None


def init(user_auth):
    global reddit

    reddit = praw.Reddit(client_id=user_auth['client_id'],
                         client_secret=user_auth['client_secret'],
                         user_agent=user_auth['user_agent'])


def get_urls():
    urls = []

    subreddit = reddit.subreddit('giveaways')
    submissions_top = subreddit.search("flair:'gleam'", sort='top', time_filter='week')
    submissions_new = subreddit.search("flair:'gleam'", sort='new')

    for submission in itertools.chain(submissions_top, submissions_new):
        url = submission.url
        title = submission.title
        if (re.search('{WW}|{\?\?}|{ww}|{Ww}', title) or title.count('{') == 0) and url.count('https://gleam.io/') > 0:
            urls.append(url)

    # remove unnecessary arguments
    urls = [url[:url.find('?')] if url.count('?') > 0 else url for url in urls]

    # remove duplicates
    urls = list(dict.fromkeys(urls))

    return urls
