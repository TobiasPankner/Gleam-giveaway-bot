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

    print(f"Pulling links from /r/giveaways")

    subreddit = reddit.subreddit('giveaways')
    submissions_top = subreddit.top(time_filter='week', limit=100)
    submissions_new = subreddit.new(limit=None)

    for submission in submissions_top:
        url = submission.url
        title = submission.title
        if (re.search('{WW}|{\?\?}|{ww}|{Ww}', title) or title.count('{') == 0) and url.count('https://gleam.io/') > 0:
            urls.append(url)

    for submission in submissions_new:
        url = submission.url
        title = submission.title
        if (re.search('{WW}|{\?\?}|{ww}|{Ww}', title) or title.count('{') == 0) and url.count('https://gleam.io/') > 0:
            urls.append(url)

    # remove unnecessary arguments
    urls = [url[:url.find('?')] if url.count('?') > 0 else url for url in urls]

    # remove duplicates
    urls = list(dict.fromkeys(urls))

    print(f"Pulled {len(urls)} links from /r/giveaways\n")

    return urls
