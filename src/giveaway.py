import json
import time
from enum import Enum

import colored
from colored import stylize

from src import utils, gleam, playrgg

entry_types = None
config = None


def load_json():
    global entry_types, config

    with open('data/entry_types.json') as json_data_file:
        entry_types = json.load(json_data_file)

    with open('config.json') as json_data_file:
        config = json.load(json_data_file)


class GiveawayTypes(Enum):
    UNKNOWN = 0
    GLEAM = 1
    PLAYRGG = 2


class Giveaway:
    def __init__(self, url, info=None, name=""):
        self.id = utils.extract_id_from_url(url)
        self.info = info
        self.name = name

        if self.id is None:
            raise ValueError

        if url.count("gleam.io") > 0:
            self.type = GiveawayTypes.GLEAM
            self.url = f"https://gleam.io/{self.id}/a"

        elif url.count("playr.gg") > 0:
            self.type = GiveawayTypes.PLAYRGG
            self.url = f"https://playr.gg/giveaway/{self.id}"
        else:
            self.type = GiveawayTypes.UNKNOWN
            self.url = url

    def get_info(self, after_giveaway=False):
        if self.type == GiveawayTypes.GLEAM:
            giveaway_info, user_info = gleam.get_info()

            if giveaway_info is None:
                raise ValueError

            if 'authentications' not in user_info['contestant']:
                print("Not logged in with name+email")
                raise ValueError

            whitelist = gleam.make_whitelist(entry_types, user_info)

            self.name = giveaway_info['campaign']['name']
            self.info = {"giveaway_info": giveaway_info, "user_info": user_info, "whitelist": whitelist}

        elif self.type == GiveawayTypes.PLAYRGG:
            info = playrgg.get_info(self.id)

            if info is None:
                raise ValueError

            self.name = info['title']
            self.info = info

            if after_giveaway:
                success_str = stylize("\n\tDid entry method: {id} ({method})", colored.fg("green"))
                fail_str = stylize("\n\tDid entry method: {id} ({method})", colored.fg("red"))
                couldnt_see_str = stylize("\n\tCouldn't see entry method: {id} ({method})", colored.fg("grey_46"))

                to_print_list = []
                for entry_method in info['entryMethods']:
                    if entry_method['completion_status'] == 'c':
                        to_print_list.append(success_str.format(**entry_method))
                    elif entry_method['completion_status'] == 'cns':
                        to_print_list.append(couldnt_see_str.format(**entry_method))
                    else:
                        to_print_list.append(fail_str.format(**entry_method))

                print(''.join(to_print_list[:-1]), end='')

        else:
            raise ValueError

    def complete(self):
        if self.type == GiveawayTypes.GLEAM:
            giveaway_info = self.info['giveaway_info']

            # complete additional details like date of birth
            if giveaway_info['campaign']['additional_contestant_details']:
                print("\n\tCompleting additional details", end='')
                if 'gleam' in config:
                    success = gleam.complete_additional_details(giveaway_info, config['gleam'])
                    if not success:
                        print("\r\tFailed to complete additional details               ", end='')
                        raise ValueError

                    time.sleep(1)
                    print("\r\tCompleted additional details                  ")

            gleam.do_giveaway(self.info)

        elif self.type == GiveawayTypes.PLAYRGG:
            print("\n\tCompleting giveaway", end='')
            playrgg.do_giveaway(self.info)
            print("\r\tCompleted giveaway                  ")



