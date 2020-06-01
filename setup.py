import json

from src import browser

if __name__ == '__main__':
    with open('config.json') as json_data_file:
        config = json.load(json_data_file)

    browser.init_driver(config['user-data-dir'], config['profile-directory'], headless=False)
    browser.get_url("https://gleam.io/examples/competitions/every-entry-type")

    input("Press any button when finished logging in\n")

    browser.save_cookies()
    browser.close_driver()

    print("Successfully saved authentication cookies")
