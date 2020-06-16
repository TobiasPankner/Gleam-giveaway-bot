import datetime
import re
import time

from requests import get
from selenium.common import exceptions

from src import browser, twitter, giveaway


def get_info(id_token):
    url_contest = f'https://api.playr.gg/graphql?operationName=contestShow&variables={{"idToken":"{id_token}"}}&extensions={{"persistedQuery":{{"version":1,"sha256Hash":"5cc2af3aa6ca938f25d28173301bbe132f587012c26b3f8904a3e475896ec13c"}}}}'

    response = get(url_contest)
    if response.status_code != 200:
        raise giveaway.PageNotAvailableError

    result = response.json()['data']['contest']

    # sort the entry methods
    result['entryMethods'].sort(key=lambda x: x['order'])

    # convert the end-time to timestamp and add it to the info
    t = result['expiration']
    end_time = time.mktime(datetime.datetime.strptime(t, "%Y-%m-%dT%H:%M:%SZ").timetuple())
    result["expiration_unix"] = int(end_time)

    # wait until the giveaway is loaded
    if browser.wait_until_found(f"div[id='{id_token}']:not(.loading-wrap)", 7) is None:
        raise giveaway.PageNotAvailableError

    # check if the giveaway has ended
    if browser.driver.current_url.count("ended") > 0:
        raise giveaway.EndedError

    # check if the giveaway is available in the users country
    if browser.get_elem_by_css(".contest-notifications__warnings") is not None:
        raise giveaway.CountryError

    # check the completion status of the entry methods
    for entry_method in result['entryMethods']:
        elem = browser.get_elem_by_css(f"div[id^='method-{entry_method['id']}']")
        if elem is None or not elem.is_displayed():
            # could not see
            entry_method['completion_status'] = "cns"
            continue

        classes = elem.get_attribute("class")
        class_list = classes.split(' ')

        if 'contest-entry-join-wrap--entered' in class_list:
            # completed
            entry_method['completion_status'] = "c"
            continue
        else:
            # not completed
            entry_method['completion_status'] = "nc"
            continue

    return result


def do_giveaway(info):
    popups_disabled = False
    main_window = browser.driver.current_window_handle

    blacklist = ['twitch_subscription', 'secret_code', 'affiliate_link', 'donation']

    if browser.wait_until_found(f"div[id='{info['idToken']}']:not(.loading-wrap)", 4) is None:
        return

    # put the completion_bonus entry methods last
    entry_methods_completion_bonus = [entry_method for entry_method in info['entryMethods'] if entry_method['method'] == 'completion_bonus']
    entry_methods = [entry_method for entry_method in info['entryMethods'] if entry_method['method'] != 'completion_bonus']

    entry_methods.extend(entry_methods_completion_bonus)

    # if not all entry methods are shown at the start set waited_for_other_entries to False
    waited_for_other_entries = all(not entry_method['required'] for entry_method in entry_methods)

    for entry_method in info['entryMethods']:
        if entry_method['method'] in blacklist or entry_method['completion_status'] == 'c':
            # ignored or completed
            continue

        # when the first entry methods that requires other to be completed comes up, wait 2 seconds
        if not entry_method['required'] and not waited_for_other_entries:
            time.sleep(2)
            waited_for_other_entries = True

        elem = browser.get_elem_by_css(f"div[id^='method-{entry_method['id']}']")

        if not elem:
            # not visible
            continue

        try:
            elem.click()
        except (exceptions.ElementNotInteractableException, exceptions.ElementClickInterceptedException):
            continue

        time.sleep(0.5)

        do_entry(elem, entry_method)

        browser.driver.switch_to.window(main_window)

        if not popups_disabled:
            popups_disabled = disable_popups()

    browser.cleanup_tabs()


def do_entry(entry_method_elem, entry_method):
    method = entry_method['method']
    meta = entry_method['meta'] if 'meta' in entry_method else {}

    if method.count("twitter") > 0:
        if method == 'twitter_follow':
            name = meta['twitter_name']
            twitter.follow(name)

        elif method == 'twitter_retweet':
            match = re.search(r"twitter\.com\/.*\/status(?:es)?\/([^\/\?]+)", meta['tweet_link'])
            if not match:
                return

            tweet_id = match.group(1)

            tweet_id = tweet_id.replace("status/", "")
            twitter.retweet(tweet_id)

        elif method == 'twitter_tweet':
            text = meta['tweet_text']
            twitter.tweet(text)

        elif method == 'twitter_hashtag':
            text = '#' + meta['hashtag']
            twitter.tweet(text)

        try:
            already_done_elem = entry_method_elem.find_element_by_css_selector("button.btn-link")
        except exceptions.NoSuchElementException:
            return

        try:
            already_done_elem.click()
        except exceptions.ElementNotInteractableException:
            return

    elif method == 'mailing_list':
        pass

    else:
        button_elem = get_primary_button(entry_method['id'])

        if button_elem is None:
            return

        try:
            button_elem.click()
        except (exceptions.ElementNotInteractableException , exceptions.ElementClickInterceptedException):
            return

        if method == 'twitch_follow' or method == 'mixer_follow' or method == 'playr_follow':
            return

        time.sleep(1)
        browser.cleanup_tabs()


def get_primary_button(entry_method_id):
    return browser.wait_until_found(f"div[id^='method-{entry_method_id}'] > * .btn-playr-primary", 2)


def disable_popups():
    other_giveaways_pop = browser.get_elem_by_css("span.toast-wrap")
    if other_giveaways_pop is not None:
        browser.driver.execute_script("arguments[0].style.display = 'none';", other_giveaways_pop)

    point_pop = browser.get_elem_by_css("div.iziToast-wrapper")
    if point_pop is None:
        return False

    browser.driver.execute_script("arguments[0].style.display = 'none';", point_pop)

    return True
