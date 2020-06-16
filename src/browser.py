import pickle
import time

from selenium import webdriver
from selenium.common import exceptions
from selenium.webdriver import DesiredCapabilities
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

driver: webdriver.Chrome = None
storage = None


class LocalStorage:
    def __init__(self, driver_to_attach):
        self.driver = driver_to_attach

    def __len__(self):
        return self.driver.execute_script("return window.localStorage.length;")

    def items(self):
        return self.driver.execute_script(
            "var ls = window.localStorage, items = {}; ""for (var i = 0, k; i < ls.length; ++i) ""  items[k = ls.key(i)] = ls.getItem(k); ""return items; ")

    def keys(self):
        return self.driver.execute_script(
            "var ls = window.localStorage, keys = []; "
            "for (var i = 0; i < ls.length; ++i) "
            "  keys[i] = ls.key(i); "
            "return keys; ")

    def get(self, key):
        return self.driver.execute_script("return window.localStorage.getItem(arguments[0]);", key)

    def set(self, key, value):
        self.driver.execute_script("window.localStorage.setItem(arguments[0], arguments[1]);", key, value)

    def has(self, key):
        return key in self.keys()

    def remove(self, key):
        self.driver.execute_script("window.localStorage.removeItem(arguments[0]);", key)

    def clear(self):
        self.driver.execute_script("window.localStorage.clear();")

    def __getitem__(self, key):
        value = self.get(key)
        if value is None:
            raise KeyError(key)
        return value

    def __setitem__(self, key, value):
        self.set(key, value)

    def __contains__(self, key):
        return key in self.keys()

    def __iter__(self):
        return self.items().__iter__()

    def __repr__(self):
        return self.items().__str__()


def init_driver(user_data_dir="", profile_dir="", headless=True):
    global driver, storage

    options = Options()

    if headless:
        options.add_argument("--headless")

        # disable image loading
        chrome_prefs = {}
        options.experimental_options["prefs"] = chrome_prefs
        chrome_prefs["profile.default_content_settings"] = {"images": 2}
        chrome_prefs["profile.managed_default_content_settings"] = {"images": 2}

    elif user_data_dir != "":
        options.add_argument(f"user-data-dir={user_data_dir}")
        options.add_argument(f"profile-directory={profile_dir}")

    options.add_experimental_option('excludeSwitches', ['enable-logging'])

    # Page load strategy none doesnt wait for the page to fully load before continuing
    caps = DesiredCapabilities().CHROME
    caps["pageLoadStrategy"] = "none"

    driver = webdriver.Chrome(ChromeDriverManager().install(), chrome_options=options, desired_capabilities=caps)

    storage = LocalStorage(driver)


def close_driver():
    global driver, storage

    if driver:
        driver.quit()

    driver = None
    storage = None


def save_cookies(filename):
    if driver is not None:
        pickle.dump(driver.get_cookies(), open(filename, "wb"))


def load_cookies(filename):
    for cookie in pickle.load(open(filename, "rb")):
        if 'expiry' in cookie:
            del cookie['expiry']

        driver.add_cookie(cookie)


def apply_cookies(url):
    if driver:
        get_url(url)
        time.sleep(0.5)
        send_escape_global()
        if url.count("gleam.io") > 0:
            load_cookies("data/cookies.pkl")
        else:
            load_cookies("data/cookies_playrgg.pkl")


def get_url(url):
    driver.switch_to.default_content()
    driver.get(url)


def refresh():
    driver.refresh()


def send_escape_global():
    webdriver.ActionChains(driver).send_keys(Keys.ESCAPE).perform()


def cleanup_tabs():
    # close all other tabs
    tabs = driver.window_handles
    if len(tabs) > 1:
        for handle in tabs[1:]:
            driver.switch_to.window(handle)
            send_escape_global()
            driver.close()

        driver.switch_to.window(tabs[0])


def get_elem_by_css(selector):
    try:
        elem = driver.find_element_by_css_selector(selector)
    except exceptions.NoSuchElementException:
        return None

    return elem


def get_elems_by_css(selector):
    try:
        elems = driver.find_elements_by_css_selector(selector)
    except exceptions.NoSuchElementException:
        return []

    return elems


def wait_until_found(sel, timeout, display=True):
    try:
        element_present = EC.presence_of_element_located((By.CSS_SELECTOR, sel))
        WebDriverWait(driver, timeout).until(element_present)

        return driver.find_element_by_css_selector(sel)
    except exceptions.TimeoutException:
        if display:
            print(f"Timeout waiting for element. ({sel})")
        return None
