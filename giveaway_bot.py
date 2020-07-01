import json
import os

from src import browser, giveaway, logger, reddit, scraper, twitter, utils


def main():
    giveaway.load_json()

    history_ids = logger.read_log("data/history.csv")
    error_ids = logger.read_log("data/errors.csv")

    with open('config.json') as json_data_file:
        config = json.load(json_data_file)

    if not os.path.isfile("data/cookies.pkl"):
        print("Did not find a authentication cookies file, please run login.py first")
        exit(0)

    if config['do_playrgg_giveaways'] and not os.path.isfile("data/cookies_playrgg.pkl"):
        print("If you want to complete playrgg giveaways, first run login.py and complete the steps.")
        exit(0)

    # Get all the giveaway urls
    utils.start_loading_text("Getting urls from https://reddit.com/r/giveaways/")
    urls_reddit = reddit.get_urls()

    urls = urls_reddit['gleam'].copy()
    if config['do_playrgg_giveaways']:
        urls.extend(urls_reddit['playrgg'])

    utils.stop_loading_text(f"Got {len(urls)} urls from https://reddit.com/r/giveaways/")

    utils.start_loading_text("Getting urls from http://gleamlist.com")
    urls_gleamlist = scraper.get_urls_gleamlist()
    utils.stop_loading_text(f"Got {len(urls_gleamlist)} urls from http://gleamlist.com")

    urls.extend(urls_gleamlist)

    if config['do_playrgg_giveaways']:
        utils.start_loading_text("Getting urls from https://playr.gg/giveaways")
        urls_playrgg = scraper.get_urls_playrgg()
        utils.stop_loading_text(f"Got {len(urls_playrgg)} urls from https://playr.gg/giveaways")

        urls.extend(urls_playrgg)

    giveaways = []
    for url in urls:
        try:
            giveaways.append(giveaway.Giveaway(url))
        except ValueError:
            continue

    giveaways = utils.filter_giveaways(giveaways, history_ids, error_ids)

    print(f"\nTotal givewaways after filtering: {len(giveaways)}")

    if config['twitter_auth']['consumer_key'] != "":
        twitter.init(config['twitter_auth'])
    else:
        print("Not using twitter, no details given in the config")

    browser.init_driver()

    # load the cookies
    browser.apply_cookies("https://gleam.io/")
    if config['do_playrgg_giveaways']:
        browser.apply_cookies("https://playr.gg/")

    # complete the giveaways
    for g in giveaways:
        print("\n")
        browser.get_url(g.url)
        print(f"Visited {g.url}")

        try:
            g.get_info()

            print(g.name, end='', flush=True)

            g.complete()

            # update the info
            browser.refresh()

            g.get_info(after_giveaway=True)

        except giveaway.CountryError:
            print("\tNot available in your country", end='')
            logger.write_error("data/errors.csv", g)
            continue

        except giveaway.EndedError:
            print("\tGiveaway has ended", end='')
            logger.write_error("data/errors.csv", g)
            continue

        except giveaway.NotStartedError:
            print("\tGiveaway has not started yet", end='')
            continue

        except giveaway.PageNotAvailableError:
            print("\tError getting page information or page does not exist", end='')
            logger.write_error("data/errors.csv", g)
            continue

        except giveaway.NotLoggedInError:
            print("\tNot logged in, please run login.py", end='')
            continue

        except giveaway.CaptchaError:
            print("\tGiveaway requires Human Verification", end='')
            logger.write_error("data/errors.csv", g)
            continue

        except ValueError:
            logger.write_error("data/errors.csv", g)
            continue

        logger.write_log("data/history.csv", g)


if __name__ == '__main__':
    try:
        main()
    finally:
        utils.stop_loading_text()
        browser.close_driver()
