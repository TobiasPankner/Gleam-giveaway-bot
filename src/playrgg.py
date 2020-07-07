import datetime
import json
import pickle
import re
import time

import requests
from requests_toolbelt import threaded
from selenium.common import exceptions

from src import browser, twitter, giveaway

cookies = []


def load_cookies(filename):
    global cookies

    with open(filename, 'rb') as f:
        cookies = pickle.load(f)


def extract_bearer_from_cookies():
    for cookie in cookies:
        if 'name' in cookie and cookie['name'] == "playr_production_v2_token":
            return cookie['value']


def get_info(id_token):
    info_dict = {}

    if len(cookies) == 0:
        load_cookies("data/cookies_playrgg.pkl")

    bearer_token = extract_bearer_from_cookies()
    if bearer_token is None:
        raise giveaway.NotLoggedInError

    url_me = 'https://api.playr.gg/graphql?operationName=me&variables={}&extensions={"persistedQuery":{"version":1,"sha256Hash":"4400523464928f24a8872f40f005c5192b51de9f39c69b306441fe10f77afc6f"}}'
    url_interactions = f'https://api.playr.gg/graphql?operationName=contestInteractions&variables={{"idTokens":["{id_token}"]}}&extensions={{"persistedQuery":{{"version":1,"sha256Hash":"89a49def37b638a67593f43834fe72660297b02a281b8472877a8dac918a10fd"}}}}'
    url_contest = f'https://api.playr.gg/graphql?operationName=contestShow&variables={{"idToken":"{id_token}"}}&extensions={{"persistedQuery":{{"version":1,"sha256Hash":"4e841e35d27843627b6f970c484af73576bbac0b29e47ff73e63b81bcd3b4d66"}}}}'

    requests = [{
        'method': 'GET',
        'url': url_me,
        'headers': {"Authorization": f"Bearer {bearer_token}"}
    }, {
        'method': 'GET',
        'url': url_interactions,
        'headers': {"Authorization": f"Bearer {bearer_token}"}
    }, {
        'method': 'GET',
        'url': url_contest
    }]

    responses_generator, exceptions_generator = threaded.map(requests)
    for response in responses_generator:
        if response.status_code != 200:
            raise giveaway.PageNotAvailableError

        response_json = response.json()

        if 'data' not in response_json:
            raise giveaway.PageNotAvailableError

        response_json = response_json['data']

        if response.url.count("contestInteractions") > 0:
            info_dict['contestInteractions'] = response_json['me']['contestInteractions']

        elif response.url.count("contestShow") > 0:
            contest = response_json['contest']

            # sort the entry methods
            contest['entryMethods'].sort(key=lambda x: x['order'])

            # convert the end-time to timestamp and add it to the info
            t = contest['expiration']
            end_time = time.mktime(datetime.datetime.strptime(t, "%Y-%m-%dT%H:%M:%SZ").timetuple())
            contest["expiration_unix"] = int(end_time)

            info_dict['contest'] = response_json['contest']

        else:
            info_dict['user'] = response_json['me']

    # check for errors

    # wait until the giveaway is loaded
    if wait_for_giveaway(info_dict['contest']['idToken']) is None:
        raise giveaway.PageNotAvailableError

    # check if the giveaway has ended
    if browser.driver.current_url.count("ended") > 0:
        raise giveaway.EndedError

    # check if the giveaway is available
    if browser.driver.current_url.count("not-found") > 0:
        raise giveaway.PageNotAvailableError

    # check if the giveaway is available in the users country
    if browser.get_elem_by_css(".contest-notifications__warnings") is not None:
        raise giveaway.CountryError

    # get the ids of the completed entry methods
    completed_entry_ids = []
    for completed_entry in info_dict['contestInteractions'][0]['entries']:
        completed_entry_ids.append(completed_entry['entryMethodId'])

    # add a completion status to the entry methods
    for entry in info_dict['contest']['entryMethods']:
        if int(entry['id']) in completed_entry_ids:
            entry['completion_status'] = 'c'

        else:
            elem = browser.get_elem_by_css(f"div[id^='method-{entry['id']}']")
            if elem is None or not elem.is_displayed():
                # couldn't see element
                entry['completion_status'] = 'cns'
            else:
                entry['completion_status'] = 'nc'

    return info_dict


def make_whitelist(entry_types, info):
    whitelist = []

    integrations = info['user']['integrations']
    providers = [integration['provider'] for integration in integrations]

    for provider in providers:
        if provider in entry_types:
            whitelist.extend(entry_types[provider])

    whitelist.extend(entry_types['other'])
    whitelist.extend(entry_types['visit_click'])

    return whitelist


def do_giveaway(info):
    popups_disabled = False
    main_window = browser.driver.current_window_handle

    whitelist = info['whitelist']
    info = info['contest']

    # put the completion_bonus entry methods last
    entry_methods_completion_bonus = [entry_method for entry_method in info['entryMethods'] if entry_method['method'] == 'completion_bonus']
    entry_methods = [entry_method for entry_method in info['entryMethods'] if entry_method['method'] != 'completion_bonus']

    entry_methods.extend(entry_methods_completion_bonus)

    # if not all entry methods are shown at the start set waited_for_other_entries to False
    waited_for_other_entries = all(not entry_method['required'] for entry_method in entry_methods)

    for entry_method in info['entryMethods']:
        if entry_method['method'] not in whitelist or entry_method['completion_status'] == 'c':
            # ignored or completed
            continue

        # when the first entry methods that requires other to be completed comes up, wait 2 seconds
        if not entry_method['required'] and not waited_for_other_entries:
            browser.refresh()
            wait_for_giveaway(info['idToken'])
            waited_for_other_entries = True

        elem = browser.get_elem_by_css(f"div[id^='method-{entry_method['id']}']")

        if elem is None or not elem.is_displayed():
            # not visible
            continue

        do_entry(elem, entry_method, info['id'])

        browser.driver.switch_to.window(main_window)

        time.sleep(0.2)

        if not popups_disabled:
            popups_disabled = disable_popups()

    browser.cleanup_tabs()


def do_entry(entry_method_elem, entry_method, contest_id):
    method = entry_method['method']
    meta = entry_method['meta'] if 'meta' in entry_method else {}

    if method.count("twitter") > 0:
        try:
            entry_method_elem.click()
        except (exceptions.ElementNotInteractableException, exceptions.ElementClickInterceptedException):
            return

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

        already_done_elem = get_already_done_button(entry_method['id'])

        if already_done_elem is None:
            return

        try:
            already_done_elem.click()
        except exceptions.ElementNotInteractableException:
            return

    elif method == 'twitch_follow' or method == 'mixer_follow' or method == 'playr_follow':
        try:
            entry_method_elem.click()
        except (exceptions.ElementNotInteractableException, exceptions.ElementClickInterceptedException):
            return

        time.sleep(0.25)

        button_elem = get_primary_button(entry_method['id'])

        if button_elem is None:
            return

        try:
            button_elem.click()
        except (exceptions.ElementNotInteractableException, exceptions.ElementClickInterceptedException):
            return

    else:
        data = {"entry_method": entry_method}
        bearer = extract_bearer_from_cookies()
        headers = {'content-type': 'application/json', "Authorization": f"Bearer {bearer}"}

        new_cookies = {}
        for cookie in cookies:
            new_cookies[cookie['name']] = cookie['value']

        requests.post(f"https://playr.gg/api/v1/contests/{contest_id}/entries", data=json.dumps(data), headers=headers,
                      cookies=new_cookies)


def get_primary_button(entry_method_id):
    return browser.wait_until_found(f"div[id^='method-{entry_method_id}'] > * .btn-playr-primary", 2)


def get_already_done_button(entry_method_id):
    return browser.wait_until_found(f"div[id^='method-{entry_method_id}'] > * button.btn-link", 2)


def disable_popups():
    other_giveaways_pop = browser.get_elem_by_css("span.toast-wrap")
    if other_giveaways_pop is not None:
        browser.driver.execute_script("arguments[0].style.display = 'none';", other_giveaways_pop)

    point_pop = browser.get_elem_by_css("div.iziToast-wrapper")
    if point_pop is None:
        return False

    browser.driver.execute_script("arguments[0].style.display = 'none';", point_pop)

    return True


def wait_for_giveaway(id_token):
    return browser.wait_until_found(f"div[id='{id_token}']:not(.loading-wrap)", 7)
