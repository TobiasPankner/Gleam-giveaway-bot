import re
import time

import requests


def get_submissions(size):
    to_return_list = []
    size_remaining = size
    error_cnt = 0
    before = int(time.time())

    while size_remaining != 0:
        if error_cnt > 3:
            break

        if size_remaining > 500:
            url = f"https://api.pushshift.io/reddit/submission/search/?sort_type=created_utc&subreddit=giveaways&size=500&before={before}&fields=url,link_flair_text,title,retrieved_on"
        else:
            url = f"https://api.pushshift.io/reddit/submission/search/?sort_type=created_utc&subreddit=giveaways&size={size_remaining}&before={before}&fields=url,link_flair_text,title,retrieved_on"

        api_result = requests.get(url)
        if api_result.status_code != 200:
            error_cnt += 1
            continue

        last_retrieved = api_result.json()['data']
        to_return_list.extend(last_retrieved)
        for i in range(10):
            try:
                before = last_retrieved[len(last_retrieved) - 1 - i]['retrieved_on']
            except ValueError:
                pass
            break

        size_remaining = size_remaining - len(last_retrieved)

    return to_return_list


def get_urls():
    gleam_urls = []
    playrgg_urls = []
    return_dict = {"gleam": [], "playrgg": []}

    submissions = get_submissions(1500)

    for submission in submissions:
        # if the giveaway is not available worldwide, discard it
        if not re.search(r'{WW}|{\?\?}|{ww}|{Ww}', submission['title']) and submission['title'].count('{') > 0:
            continue

        url = submission['url']
        url = url[:url.find('?')] if url.count('?') > 0 else url

        # if either the flair or the url contains the word "gleam" treat it as a gleam giveaway
        if 'link_flair_text' in submission and submission['link_flair_text'].lower().count("gleam") > 0 or url.count(
                "gleam.io") > 0:
            gleam_urls.append(url)

        elif 'link_flair_text' in submission and submission['link_flair_text'].lower().count(
                "playrgg") > 0 or url.count("playr.gg") > 0:
            playrgg_urls.append(url)

        else:
            continue

    gleam_urls = list(dict.fromkeys(gleam_urls))
    return_dict['gleam'] = gleam_urls

    playrgg_urls = list(dict.fromkeys(playrgg_urls))
    return_dict['playrgg'] = playrgg_urls

    return return_dict
