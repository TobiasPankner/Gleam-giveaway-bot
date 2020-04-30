import json
import re

from src import reddit, browser_actions, twitter, logger, scraper

if __name__ == '__main__':
    history_ids = logger.read_log("data/history.csv")

    with open('config.json') as json_data_file:
        config = json.load(json_data_file)

    with open('data/entry_types.json') as json_data_file:
        entry_types = json.load(json_data_file)

    reddit.init(config['reddit_auth'])
    twitter.init(config['twitter_auth'])

    urls_reddit = reddit.get_urls()
    urls_gleamlist = scraper.get_urls_gleamlist()

    urls = urls_reddit.copy()
    urls.extend(urls_gleamlist)

    print(f"Total links: {len(urls)}")

    # remove unnecessary info of the url and ignore previously visited
    for i, url in enumerate(urls):
        id_re = re.search(r"\w+/(\w+)[/-]", url)
        if not id_re:
            continue

        id_str = id_re.group(1)

        new_url = f"https://gleam.io/{id_str}/a"
        if id_str not in history_ids:
            urls[i] = new_url
        else:
            urls[i] = ""

    urls = [url for url in urls if url != ""]
    urls = list(dict.fromkeys(urls))

    print(f"Total links after duplicate removal: {len(urls)}")

    #urls = ["https://gleam.io/examples/competitions/every-entry-type"]

    browser_actions.init_driver()

    for url in urls:
        browser_actions.get_url(url)
        print(f"\nVisited {url}")

        giveaway_info, user_info = browser_actions.get_gleam_info()

        if giveaway_info is None:
            continue

        whitelist = browser_actions.make_whitelist(entry_types, user_info)

        browser_actions.do_giveaway(giveaway_info, whitelist)

        # update the info
        browser_actions.refresh()
        giveaway_info, user_info = browser_actions.get_gleam_info()

        logger.write_log("data/history.csv", giveaway_info, user_info)

