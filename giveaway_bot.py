import json
import os

from src import reddit, gleam, twitter, logger, scraper, utils, browser


def main():
    if not os.path.isfile("data/cookies.pkl"):
        print("Did not find a authentication cookies file, please run login.py first")
        exit(0)

    history_ids = logger.read_log("data/history.csv")
    error_ids = logger.read_log("data/errors.csv")

    with open('config.json') as json_data_file:
        config = json.load(json_data_file)

    with open('data/entry_types.json') as json_data_file:
        entry_types = json.load(json_data_file)

    if config['reddit_auth']['client_id'] != "":
        reddit.init(config['reddit_auth'])

        utils.start_loading_text("Getting urls from https://reddit.com/r/giveaways/")
        urls_reddit = reddit.get_urls()
        utils.stop_loading_text(f"Got {len(urls_reddit)} urls from https://reddit.com/r/giveaways/")

        urls = urls_reddit.copy()
    else:
        print("Not using reddit, no details given in the config")
        urls = []

    utils.start_loading_text("Getting urls from http://gleamlist.com")
    urls_gleamlist = scraper.get_urls_gleamlist()
    utils.stop_loading_text(f"Got {len(urls_gleamlist)} urls from http://gleamlist.com")

    urls.extend(urls_gleamlist)

    print(f"\nTotal urls: {len(urls)}")

    urls = utils.filter_urls(urls, history_ids, error_ids)

    print(f"After duplicate removal: {len(urls)}")

    if config['twitter_auth']['consumer_key'] != "":
        twitter.init(config['twitter_auth'])
    else:
        print("Not using twitter, no details given in the config")

    browser.init_driver(config['user-data-dir'], config['profile-directory'], load_cookies_url="https://gleam.io")

    for url in urls:
        print("\n")
        utils.start_loading_text(f"Visiting {url}")
        browser.get_url(url)
        utils.stop_loading_text(f"Visited {url}")

        giveaway_info, user_info = gleam.get_info()

        if giveaway_info is None:
            logger.write_error("data/errors.csv", url)
            continue

        if 'authentications' not in user_info['contestant']:
            print("Not logged in with name+email")
            exit(0)

        print(giveaway_info['campaign']['name'], end='')

        whitelist = gleam.make_whitelist(entry_types, user_info)

        # complete additional details like date of birth
        if giveaway_info['campaign']['additional_contestant_details']:
            print("\n\tCompleting additional details", end='')
            if 'gleam' in config:
                success = gleam.complete_additional_details(giveaway_info, config['gleam'])
                if not success:
                    logger.write_log("data/history.csv", giveaway_info, user_info)
                    print("\r\tFailed to complete additional details               ")
                    continue
                print("\r\tCompleted additional details                  ")

        gleam.do_giveaway(giveaway_info, whitelist)

        # update the info
        browser.refresh()
        giveaway_info, user_info = gleam.get_info()

        if giveaway_info is None:
            logger.write_error("data/errors.csv", url)
            print("Could not write log")
            continue

        logger.write_log("data/history.csv", giveaway_info, user_info)


if __name__ == '__main__':
    try:
        main()
    finally:
        utils.stop_loading_text()
        browser.close_driver()
