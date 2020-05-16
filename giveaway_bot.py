import json
import os

from src import reddit, browser_actions, twitter, logger, scraper, utils


def main():
    history_ids = logger.read_log("data/history.csv")

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

    urls = utils.filter_urls(urls, history_ids)

    print(f"After duplicate removal: {len(urls)}")

    if config['twitter_auth']['consumer_key'] != "":
        twitter.init(config['twitter_auth'])
    else:
        print("Not using twitter, no details given in the config")

    if not os.path.isfile("data/cookies.pkl") or input("\nBegin [b] Setup [s] ") == 's':
        browser_actions.init_driver(config['user-data-dir'], config['profile-directory'], headless=False)
        browser_actions.get_url("https://gleam.io/examples/competitions/every-entry-type")

        input("\nPress any button when finished logging in\n")

        browser_actions.save_cookies()
        browser_actions.close_driver()

    utils.start_loading_text("Starting webdriver in headless mode")
    browser_actions.init_driver(config['user-data-dir'], config['profile-directory'])
    utils.stop_loading_text("Started webdriver in headless mode")

    for url in urls:
        print("\n")
        utils.start_loading_text(f"Visiting {url}")
        browser_actions.get_url(url)
        utils.stop_loading_text(f"Visited {url}")

        giveaway_info, user_info = browser_actions.get_gleam_info()

        if giveaway_info is None:
            continue

        if 'authentications' not in user_info['contestant']:
            print("Not logged in with name+email")
            exit(0)

        print(giveaway_info['campaign']['name'], end='')

        whitelist = browser_actions.make_whitelist(entry_types, user_info)

        browser_actions.do_giveaway(giveaway_info, whitelist)

        # update the info
        browser_actions.refresh()
        giveaway_info, user_info = browser_actions.get_gleam_info()

        if giveaway_info is None:
            print("Could not write log")
            continue

        logger.write_log("data/history.csv", giveaway_info, user_info)


if __name__ == '__main__':
    try:
        main()
    finally:
        utils.stop_loading_text()
