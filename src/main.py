import json

from tqdm import tqdm

from src import reddit, browser_actions, twitter, logger, scraper

if __name__ == '__main__':
    with open('../config.json') as json_data_file:
        config = json.load(json_data_file)

    with open('../data/entry_types.json') as json_data_file:
        entry_types = json.load(json_data_file)

    reddit.init(config['reddit_auth'])
    twitter.init(config['twitter_auth'])

    urls_reddit = reddit.get_urls()
    urls_gleamlist = scraper.get_urls_gleamlist()

    urls = urls_reddit.copy()
    urls.extend(urls_gleamlist)
    # remove duplicates
    urls = list(dict.fromkeys(urls))

    #urls = ["https://gleam.io/examples/competitions/every-entry-type"]

    browser_actions.init_driver()

    for url in urls:
        browser_actions.get_url(url)
        print(f"Visited {url}")

        giveaway_info, user_info = browser_actions.get_gleam_info()

        if giveaway_info is None:
            continue

        whitelist = browser_actions.make_whitelist(entry_types, user_info)

        browser_actions.do_giveaway(giveaway_info, whitelist)

        logger.write_log(giveaway_info, user_info)

