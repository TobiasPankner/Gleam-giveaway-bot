import json
import time
import urllib.parse as urlparse
from enum import Enum
from urllib.parse import parse_qs

import colored
from colored import stylize
from selenium.common import exceptions

from src import twitter, browser, giveaway


class EntryStates(Enum):
    DEFAULT = 0
    EXPANDED = 1
    COMPLETED = 2
    HIDDEN = 3


def make_whitelist(entry_types, user_info):
    whitelist = []

    auths = user_info['contestant']['authentications']

    for auth in auths:
        if auth['provider'] in entry_types:
            whitelist.extend(entry_types[auth['provider']])

    whitelist.extend(entry_types['other'])
    whitelist.extend(entry_types['visit_view'])

    return whitelist


def get_info():
    browser.cleanup_tabs()

    # check if the error image exists
    not_found_elem = browser.wait_until_found("img[src='/images/error/404.png']", 2, display=False)
    if not_found_elem:
        raise giveaway.PageNotAvailableError



    # get the giveaway webelement
    contestant_elem = browser.wait_until_found("div[ng-controller='EnterController']", 7)
    campaign_elem = browser.wait_until_found("div[ng-controller='EnterController']>div[ng-init^='initCampaign']", 1)

    if contestant_elem is None or campaign_elem is None:
        return None, None

    # get the json from the webelement attribute and parse it
    campaign_info_str = campaign_elem.get_attribute("ng-init")
    campaign_info_str = campaign_info_str.replace("initCampaign(", "")[:-1]
    campaign_info_json = json.loads(campaign_info_str)

    contestant_info_str = contestant_elem.get_attribute("ng-init")

    # extract the total entry count from the string
    entry_count = contestant_info_str[contestant_info_str.find("initEntryCount(") + 15:contestant_info_str.rfind(")")]
    entry_count = int(entry_count) if entry_count != "" else -1

    # add the number of total entries to the dict
    campaign_info_json['total_entries'] = entry_count

    contestant_info_str = contestant_info_str[contestant_info_str.find("{"):contestant_info_str.rfind("}") + 1]
    contestant_info_json = json.loads(contestant_info_str)

    if 'authentications' not in contestant_info_json['contestant']:
        raise giveaway.NotLoggedInError

    if campaign_info_json['campaign']['finished'] or campaign_info_json['campaign']['paused']:
        raise giveaway.EndedError

    if not contestant_info_json['location_allowed']:
        raise giveaway.CountryError

    if campaign_info_json['campaign']['starts_at'] > int(time.time()):
        raise giveaway.NotStartedError

    return campaign_info_json, contestant_info_json


def create_entry_method_strings(entry_method):
    entry_method_str = f"entry method: {entry_method['id']} ({entry_method['entry_type']})"
    strings = {
        "default_str":      entry_method_str,
        "success_str":      stylize(f"\r\tDid {entry_method_str}                   ",           colored.fg("green")),
        "fail_str":         stylize(f"\r\tDid {entry_method_str}                   ",           colored.fg("red")),
        "ignored_str":      stylize(f"\r\tIgnored {entry_method_str}                   ",       colored.fg("grey_46")),
        "couldnt_see_str":  stylize(f"\r\tCouldn't see {entry_method_str}                   ",  colored.fg("grey_46")),
        "will_revisit_str": stylize(f"\r\tWill revisit {entry_method_str}                   ",  colored.fg("yellow"))
    }

    return strings


def complete_additional_details(giveaway_info, gleam_config):
    details = giveaway_info['campaign']['contestant_details_groups'][0]

    fill_in_age = gleam_config['birth_day'] != "" and gleam_config['birth_month'] != "" and gleam_config['birth_year'] != ""
    accept_tac = gleam_config['accept_terms_and_services']

    # if the config says not to complete any additional details, return
    if not fill_in_age and not accept_tac:
        return False

    # get the required details
    details_required = [(name, detail) for (name, detail) in details.items() if 'required' in detail and detail['required']]

    if len(details_required) == 0:
        return True

    for (detail_name, detail_required) in details_required:
        if 'type' not in detail_required:
            continue

        # search for the visible detail element
        detail_elems = browser.get_elems_by_css(f"div[ng-init^='dc.{detail_name}']")
        visible_detail_elems = [detail_elem for detail_elem in detail_elems if detail_elem.is_displayed()]

        # if the element that requires the details was not found, an entry method has to be clicked first
        if len(visible_detail_elems) == 0:
            entry_methods = giveaway_info['entry_methods']

            # put the mandatory entry methods first
            entry_methods_not_mandatory = [entry_method for entry_method in entry_methods if not entry_method['mandatory']]
            entry_methods = [entry_method for entry_method in entry_methods if entry_method['mandatory']]
            entry_methods.extend(entry_methods_not_mandatory)

            for entry_method in entry_methods:
                try:
                    minimize_all_entries()
                except:
                    return False

                entry_method_elem, state = get_entry_elem(entry_method['id'])
                if entry_method_elem is None:
                    continue

                if state == EntryStates.DEFAULT:
                    try:
                        entry_method_elem.click()
                    except (exceptions.ElementClickInterceptedException, exceptions.ElementNotInteractableException):
                        continue

                elif state == EntryStates.HIDDEN:
                    continue

                wait_until_entry_loaded(entry_method['id'])

                # search for the visible detail element
                detail_elems = browser.get_elems_by_css(f"div[ng-init^='dc.{detail_name}']")
                visible_detail_elems = [detail_elem for detail_elem in detail_elems if detail_elem.is_displayed()]

                if len(visible_detail_elems) > 0:
                    break

        # if the details field was still not found after clicking the entry methods, return
        if len(visible_detail_elems) == 0:
            return False

        detail_elem = visible_detail_elems[0]

        if detail_required['type'] == 'checkbox':
            if 'terms_and_conditions' in detail_required and detail_required['terms_and_conditions'] and accept_tac:
                # Terms and conditions checkbox
                try:
                    to_click = detail_elem.find_element_by_css_selector(".checkbox>.icon")
                except exceptions.NoSuchElementException:
                    return False

            elif 'generated' in detail_required and detail_required['generated'] == 'minimum_age':
                # Age checkbox
                try:
                    to_click = detail_elem.find_element_by_css_selector(".checkbox>.icon")
                except exceptions.NoSuchElementException:
                    return False
            else:
                return False

            try:
                to_click.click()
            except (exceptions.ElementNotInteractableException, exceptions.ElementClickInterceptedException):
                return False

        elif detail_required['type'] == 'dob' and fill_in_age:
            # Date of birth
            try:
                enter_field = detail_elem.find_element_by_css_selector("input[age-format]")
            except exceptions.NoSuchElementException:
                return False

            if detail_required['age_format'] == "DMY":
                enter_field.send_keys(f"{int(gleam_config['birth_day']):02}{int(gleam_config['birth_month']):02}{gleam_config['birth_year']}")

            elif detail_required['age_format'] == "MDY":
                enter_field.send_keys(f"{int(gleam_config['birth_month']):02}{int(gleam_config['birth_day']):02}{gleam_config['birth_year']}")

            else:
                return False

        else:
            return False

    time.sleep(1)
    
    # Find the save/continue button
    buttons = browser.get_elems_by_css(".btn-primary:not([disabled])")
    visible_buttons = [button for button in buttons if button.is_displayed()]

    if len(visible_buttons) == 0:
        return False

    try:
        visible_buttons[0].click()
    except (exceptions.ElementNotInteractableException, exceptions.ElementClickInterceptedException):
        return False

    return True


def do_giveaway(info):
    main_window = browser.driver.current_window_handle
    elems_to_revisit = []

    giveaway_info = info['giveaway_info']
    whitelist = info['whitelist']
    campaign = giveaway_info['campaign']
    entry_methods = giveaway_info['entry_methods']

    browser.storage.clear()

    # put the mandatory entry methods first
    entry_methods_not_mandatory = [entry_method for entry_method in entry_methods if not entry_method['mandatory']]
    entry_methods = [entry_method for entry_method in entry_methods if entry_method['mandatory']]
    entry_methods.extend(entry_methods_not_mandatory)

    for entry_method in entry_methods:
        entry_method_strings = create_entry_method_strings(entry_method)

        print(f"\n\tDoing {entry_method_strings['default_str']})", end='')

        minimize_all_entries()

        if entry_method['entry_type'] not in whitelist:
            print(entry_method_strings['ignored_str'], end='')
            continue

        entry_method_elem, state = get_entry_elem(entry_method['id'])
        if entry_method_elem is None:
            continue

        if state == EntryStates.DEFAULT:
            try:
                entry_method_elem.click()
            except (exceptions.ElementClickInterceptedException, exceptions.ElementNotInteractableException):
                continue

        elif state == EntryStates.COMPLETED:
            if state == EntryStates.COMPLETED:
                print(entry_method_strings['success_str'], end='')
            else:
                print(entry_method_strings['fail_str'], end='')
            continue

        elif state == EntryStates.HIDDEN:
            print(entry_method_strings['couldnt_see_str'], end='')
            continue

        # wait for the element to be fully expanded
        wait_until_entry_loaded(entry_method['id'])

        # check if the entry method is completed after a click
        entry_method_elem, state = get_entry_elem(entry_method['id'])
        if entry_method_elem is None:
            continue

        if state == EntryStates.COMPLETED:
            print(entry_method_strings['success_str'], end='')
            continue

        to_revisit = do_entry(entry_method_elem, entry_method['entry_type'], entry_method['id'])

        if to_revisit:
            elems_to_revisit.append(entry_method)

        # get the continue button and click it
        cont_btn = get_continue_elem(entry_method_elem)
        if cont_btn is None:
            continue

        try:
            cont_btn.click()
        except (exceptions.ElementClickInterceptedException, exceptions.ElementNotInteractableException):
            pass

        # if the giveaway has a post entry url it will redirect to some other page after the last entry
        if browser.driver.current_url.count("gleam") == 0 and campaign['post_entry_url'] != "":
            browser.get_url(campaign['stand_alone_url'])

        wait_until_entry_loaded(entry_method['id'])

        entry_method_elem, state = get_entry_elem(entry_method['id'])
        if entry_method_elem is None:
            continue

        if state == EntryStates.COMPLETED:
            print(entry_method_strings['success_str'], end='')
        elif to_revisit:
            print(entry_method_strings['will_revisit_str'], end='')
        else:
            print(entry_method_strings['fail_str'], end='')

        browser.driver.switch_to.window(main_window)

    if len(elems_to_revisit) == 0:
        return

    print("\n\n\tRevisiting some entry methods:", end='')
    browser.refresh()
    for entry_method in elems_to_revisit:
        entry_method_strings = create_entry_method_strings(entry_method)

        print(f"\n\tDoing {entry_method_strings['default_str']})", end='')

        try:
            minimize_all_entries()
        except:
            return

        entry_method_elem, state = get_entry_elem(entry_method['id'])
        if entry_method_elem is None:
            continue

        if state == EntryStates.DEFAULT:
            try:
                entry_method_elem.click()
            except exceptions.ElementClickInterceptedException:
                continue
        elif state is EntryStates.COMPLETED:
            print(entry_method_strings['success_str'], end='')
        else:
            continue

        wait_until_entry_loaded(entry_method['id'])

        cont_btn = get_continue_elem(entry_method_elem)
        if cont_btn is None:
            continue

        try:
            cont_btn.click()
        except (exceptions.ElementClickInterceptedException, exceptions.ElementNotInteractableException):
            pass

        wait_until_entry_loaded(entry_method['id'])

        entry_method_elem, state = get_entry_elem(entry_method['id'])
        if entry_method_elem is None:
            continue

        if state == EntryStates.COMPLETED:
            print(entry_method_strings['success_str'], end='')
        else:
            print(entry_method_strings['fail_str'], end='')

        # time.sleep(0.5)


def do_entry(entry_method_elem, entry_type, entry_id):
    if entry_type == 'twitter_follow':
        try:
            tweet_btn = entry_method_elem.find_element_by_css_selector("div[class='expandable']>div>div>div>div>div>a")
        except exceptions.NoSuchElementException:
            return

        follow_url = tweet_btn.get_attribute("href")
        name = follow_url[follow_url.find("=") + 1:]

        twitter.follow(name)

    elif entry_type == 'twitter_retweet':
        try:
            retweet_elem = entry_method_elem.find_element_by_css_selector(
                "div[class='expandable']>div>div>div>div>div>twitter-widget")
        except exceptions.NoSuchElementException:
            return

        tweet_id = retweet_elem.get_attribute("data-tweet-id")

        twitter.retweet(tweet_id)

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

    elif entry_type == 'twitter_hashtags':
        try:
            expandable_elem = entry_method_elem.find_element_by_css_selector("div[class='expandable']")
            tweet_elem = expandable_elem.find_element_by_css_selector("a[class*='twitter']")
        except exceptions.NoSuchElementException:
            return

        tweet_url = tweet_elem.get_attribute("href")

        parsed = urlparse.urlparse(tweet_url)
        parsed = parse_qs(parsed.query)
        if 'hashtags' not in parsed:
            return

        hashtags = parsed['hashtags']
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
        except (exceptions. NoSuchElementException, exceptions.ElementClickInterceptedException, exceptions.ElementNotInteractableException):
            return

    elif entry_type.count("visit") > 0 or entry_type == 'custom_action':
        millis = int(round(time.time() * 1000))

        # set a storage entry to fake a visit
        browser.storage[f"D-{entry_id}"] = f"{{\"c\":{millis},\"o\":{{\"expires\":7}},\"v\":\"V\"}}"

        # if there is a minimum time on the entry set another storage entry
        try:
            timer_elem = entry_method_elem.find_element_by_css_selector("span[ng-hide^='!(isTimerAction']")

            if timer_elem.text.count("NaN") == 0 and timer_elem.text != "":
                browser.storage[f"T-{entry_id}"] = f"{{\"c\":{millis},\"o\":{{\"expires\":1}},\"v\":{int(time.time() - 300)}}}"

                return True
        except exceptions.NoSuchElementException:
            pass

    elif entry_type == 'loyalty':
        try:
            expandable_elem = entry_method_elem.find_element_by_css_selector("div[class='expandable']")
            claim_elem = expandable_elem.find_element_by_css_selector("span[class='tally']")
        except exceptions.NoSuchElementException:
            return

        try:
            claim_elem.click()
        except exceptions.ElementNotInteractableException:
            return

    elif entry_type == 'instagram_view_post' or entry_type == 'twitter_view_post' or entry_type == 'facebook_view_post':
        time.sleep(6)


def get_entry_elem(entry_id):
    entry_method_elem = browser.wait_until_found(f"div[class^='entry-method'][id='em{entry_id}']", 2)
    if not entry_method_elem:
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


def wait_until_entry_loaded(entry_id):
    browser.wait_until_found(f"div.entry-method[id='em{entry_id}']>a:not(.loading)", 4)


def get_continue_elem(parent_elem):
    # continue button
    try:
        cont_btn = parent_elem.find_element_by_css_selector("div[class^='form-actions']>div>a")
    except exceptions.NoSuchElementException:
        try:
            cont_btn = parent_elem.find_element_by_css_selector("div[class^='form-actions']>button")
        except exceptions.NoSuchElementException:
            try:
                cont_btn = parent_elem.find_element_by_css_selector("div[class^='form-actions']>div")
            except exceptions.NoSuchElementException:
                try:
                    cont_btn = parent_elem.find_element_by_css_selector(
                        "div[class^='form-actions']>a[ng-click^='saveEntry']")
                except exceptions.NoSuchElementException:
                    return None

    return cont_btn


def minimize_all_entries():
    entry_method_elems = browser.get_elems_by_css("div[class^='entry-method'][class*='expanded']")
    for entry_method_elem in entry_method_elems:
        try:
            entry_method_elem.click()
        except (exceptions.ElementClickInterceptedException, exceptions.ElementNotInteractableException):
            continue
