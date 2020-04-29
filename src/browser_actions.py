import json
import time
from enum import Enum

from selenium import webdriver
from selenium.common import exceptions
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import urllib.parse as urlparse
from urllib.parse import parse_qs

from src import twitter

driver: webdriver.Chrome = None


class EntryStates(Enum):
    DEFAULT = 0
    EXPANDED = 1
    COMPLETED = 2
    HIDDEN = 3


def init_driver():
    global driver

    options = Options()
    options.add_argument("user-data-dir=C:/Users/Tobias/AppData/Local/Google/Chrome/User Data")
    options.add_argument("profile-directory=Profile 2")
    # options.add_experimental_option("detach", True)
    driver = webdriver.Chrome(chrome_options=options)


def make_whitelist(entry_types, user_info):
    whitelist = []

    auths = user_info['contestant']['authentications']

    for auth in auths:
        if auth['provider'] in entry_types:
            whitelist.extend(entry_types[auth['provider']])

    whitelist.extend(entry_types['other'])
    whitelist.extend(entry_types['visit_view'])

    return whitelist


def get_url(url):
    time.sleep(3)

    driver.switch_to.default_content()
    driver.get(url)


def get_gleam_info(change_website=True):
    cur_url = driver.current_url
    campaign = None
    contestant = None

    if cur_url.count("gleam.io") > 0:
        contestant = wait_till_found("div[ng-controller='EnterController']", 7)
        campaign = wait_till_found("div[ng-controller='EnterController']>div[ng-init^='initCampaign']", 1)

    # if the info was not found it is probably in an iframe
    if campaign is None:
        iframe = wait_till_found("iframe[id^='GleamEmbed']", 7)
        if iframe is None:
            return None, None

        try:
            driver.switch_to.frame(iframe)

            contestant = wait_till_found("div[ng-controller='EnterController']", 7)
            campaign = wait_till_found("div[ng-controller='EnterController']>div[ng-init^='initCampaign']", 1)

            if campaign is None:
                driver.switch_to.default_content()
                return None, None

        except exceptions.NoSuchFrameException:
            return None, None

    campaign_info_str = campaign.get_attribute("ng-init")
    campaign_info_str = campaign_info_str.replace("initCampaign(", "")[:-1]

    campaign_info_json = json.loads(campaign_info_str)

    contestant_info_str = contestant.get_attribute("ng-init")

    entry_count = contestant_info_str[contestant_info_str.find("initEntryCount(") + 15:contestant_info_str.rfind(")")]
    entry_count = int(entry_count) if entry_count != "" else -1

    contestant_info_str = contestant_info_str[contestant_info_str.find("{"):contestant_info_str.rfind("}") + 1]

    contestant_info_json = json.loads(contestant_info_str)

    # add the number of total entries to the dict
    campaign_info_json['total_entries'] = entry_count

    # switch to the normal gleam page instead of some landing page
    if (campaign_info_json['campaign']['stand_alone_option'] == 'Page' or cur_url.count("gleam.io") == 0) and change_website:
        print(f"Changed to standalone {campaign_info_json['campaign']['stand_alone_url']}")
        get_url(campaign_info_json['campaign']['stand_alone_url'])

    return campaign_info_json, contestant_info_json


def do_giveaway(giveaway_info, whitelist):
    campaign = giveaway_info['campaign']
    entry_methods = giveaway_info['entry_methods']

    if campaign['finished'] or campaign['paused']:
        print("Giveaway has ended")
        return

    for entry_method in entry_methods:
        try:
            minimize_all_entries()
        except:
            return

        # input("Press to continue")
        if entry_method['entry_type'] not in whitelist:
            continue

        entry_method_elem, state = get_entry_elem(entry_method['id'])
        if entry_method_elem is None:
            continue

        if state == EntryStates.DEFAULT:
            entry_method_elem.click()

        elif state == EntryStates.COMPLETED or state == EntryStates.HIDDEN:
            continue

        time.sleep(2)

        do_entry(entry_method_elem, entry_method['entry_type'])

        entry_method_elem, state = get_entry_elem(entry_method['id'])
        if entry_method_elem is None:
            continue

        # continue button
        try:
            cont_btn = entry_method_elem.find_element_by_css_selector("div[class^='form-actions']>div>a")
        except exceptions.NoSuchElementException:
            try:
                cont_btn = entry_method_elem.find_element_by_css_selector("div[class^='form-actions']>button")
            except exceptions.NoSuchElementException:
                try:
                    cont_btn = entry_method_elem.find_element_by_css_selector("div[class^='form-actions']>div")
                except exceptions.NoSuchElementException:
                    continue

        try:
            cont_btn.click()
        except:
            pass

    return None


def do_entry(entry_method_elem, entry_type):
    if entry_type == 'twitter_follow':
        try:
            tweet_btn = entry_method_elem.find_element_by_css_selector("div[class='expandable']>div>div>div>div>div>a")
        except exceptions.NoSuchElementException:
            return

        follow_url = tweet_btn.get_attribute("href")
        name = follow_url[follow_url.find("=") + 1:]

        twitter.follow(name)

        time.sleep(1)

    elif entry_type == 'twitter_retweet':
        try:
            retweet_elem = entry_method_elem.find_element_by_css_selector(
                "div[class='expandable']>div>div>div>div>div>twitter-widget")
        except exceptions.NoSuchElementException:
            return

        tweet_id = retweet_elem.get_attribute("data-tweet-id")

        twitter.retweet(tweet_id)

        time.sleep(1)

    elif entry_type == 'twitter_tweet':
        try:
            tweet_elem = entry_method_elem.find_element_by_css_selector(
                "div[class='expandable']>div>div>div>div>div>a[class*='twitter']")
        except exceptions.NoSuchElementException:
            return

        tweet_url = tweet_elem.get_attribute("href")

        parsed = urlparse.urlparse(tweet_url)
        text = parse_qs(parsed.query)['text']
        if len(text) == 0:
            return
        text = text[0]

        twitter.tweet(text)

        time.sleep(1)

    elif entry_type == 'twitter_hashtags':
        try:
            expandable_elem = entry_method_elem.find_element_by_css_selector("div[class='expandable']")
            tweet_elem = expandable_elem.find_element_by_css_selector("a[class*='twitter']")
        except exceptions.NoSuchElementException:
            return

        tweet_url = tweet_elem.get_attribute("href")

        parsed = urlparse.urlparse(tweet_url)
        hashtags = parse_qs(parsed.query)['hashtags']
        if len(hashtags) == 0:
            return
        hashtags = hashtags[0].split(',')

        to_tweet = ""
        for hashtag in hashtags:
            to_tweet += f"#{hashtag} "

        twitter.tweet(to_tweet)

        try:
            already_tweeted_elem = expandable_elem.find_element_by_css_selector(
                "div>div>div>div>a[ng-click^='saveEntry']")

            already_tweeted_elem.click()
        except:
            pass

        time.sleep(1)

    elif entry_type.count("visit") > 0 or entry_type == 'custom_action':
        main_window = driver.current_window_handle
        time_to_visit = 1

        try:
            timerElem = entry_method_elem.find_element_by_css_selector("span[ng-hide^='!(isTimerAction']")
            numbers = [int(s) for s in timerElem.text.split() if s.isdigit() and 0 < int(s) < 150]
            if len(numbers) > 0:
                time_to_visit = numbers[0]
        except exceptions.NoSuchElementException:
            pass

        try:
            visit_elem = entry_method_elem.find_element_by_css_selector(
                "div[class='expandable']>div>form>div>div>a[ng-click*='Visit']")
        except exceptions.NoSuchElementException:
            try:
                visit_elem = entry_method_elem.find_element_by_css_selector(
                    "div[class='expandable']>div>form>div>div>p>a[href^='http']")
            except exceptions.NoSuchElementException:
                return

        try:
            visit_elem.click()
        except exceptions.ElementNotInteractableException:
            return

        time.sleep(time_to_visit)

        handles = driver.window_handles

        if len(handles) > 1:
            driver.switch_to.window(handles[1])
            driver.close()
            driver.switch_to.window(main_window)


def get_entry_elem(id):
    try:
        entry_method_elem = driver.find_element_by_css_selector(f"div[class^='entry-method'][id='em{id}']")
    except:
        return None, None

    state = entry_method_elem.get_attribute('class')

    if entry_method_elem.size['height'] == 0:
        state = EntryStates.HIDDEN

    elif state.count('expanded'):
        state = EntryStates.EXPANDED

    elif state.count('complete'):
        state = EntryStates.COMPLETED

    else:
        state = EntryStates.DEFAULT

    return entry_method_elem, state


def minimize_all_entries():
    entry_method_elems = driver.find_elements_by_css_selector("div[class^='entry-method'][class*='expanded']")
    for entry_method_elem in entry_method_elems:
        entry_method_elem.click()


def wait_till_found(sel, timeout):
    try:
        element_present = EC.presence_of_element_located((By.CSS_SELECTOR, sel))
        WebDriverWait(driver, timeout).until(element_present)

        return driver.find_element_by_css_selector(sel)
    except exceptions.TimeoutException:
        print(f"Timeout waiting for element. ({sel})")
        return None


def open_in_new_tab(url):
    driver.execute_script("window.open('{}');".format(url))
    handles = driver.window_handles
    driver.switch_to.window(handles[len(handles) - 1])
