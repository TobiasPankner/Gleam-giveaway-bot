import csv
import os
import time

from src.giveaway import GiveawayTypes


def write_log(filename, giveaway):
    if giveaway.type == GiveawayTypes.GLEAM:
        giveaway_info = giveaway.info['giveaway_info']
        user_info = giveaway.info['user_info']
        campaign = giveaway_info['campaign']
        contestant = user_info['contestant']

        my_entries = sum([entry[0]['w'] for entry in contestant['entered'].values()])
        available_entries = sum([int(method['worth']) for method in giveaway_info['entry_methods']])

        total_entries_int = giveaway_info['total_entries']
        total_entries = str(total_entries_int) if total_entries_int > 0 else ""
        win_chance = str(round((my_entries / total_entries_int) * 100, 4)) + '%' if giveaway_info['total_entries'] > 0 else ""

        ends_at = campaign['ends_at']

    elif giveaway.type == GiveawayTypes.PLAYRGG:
        info = giveaway.info
        entry_methods = info['entryMethods']

        my_entries = sum([entry['meta']['entry_value'] for entry in entry_methods if entry['completion_status'] == 'c' and 'entry_value' in entry['meta']])
        available_entries = sum([entry['meta']['entry_value'] for entry in entry_methods if 'entry_value' in entry['meta']])

        total_entries = ""
        win_chance = ""

        ends_at = info['expiration_unix']

    else:
        my_entries = ""
        available_entries = ""
        total_entries = ""
        win_chance = ""
        ends_at = ""

    write_header = False if os.path.isfile(filename) else True

    with open(filename, 'a', newline='') as csvfile:
        fieldnames = ['url', 'name', 'id', 'my_entries', 'available_entries', 'total_entries', 'win_chance', 'ends_at']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)

        if write_header:
            writer.writeheader()

        writer.writerow({'url': giveaway.url,
                         'name': giveaway.name.encode('ascii', 'ignore').decode(),
                         'id': giveaway.id,
                         'my_entries': str(my_entries),
                         'available_entries': str(available_entries),
                         'total_entries': str(total_entries),
                         'win_chance': str(win_chance),
                         'ends_at': str(ends_at)
                         }
                        )


def read_log(filename):
    id_set = set()

    if not os.path.isfile(filename):
        return id_set

    with open(filename, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            id_set.add(row['id'])

    return id_set


def write_error(filename, giveaway):
    timestamp = int(time.time())

    write_header = False if os.path.isfile(filename) else True

    with open(filename, 'a', newline='') as csvfile:
        fieldnames = ['id', 'timestamp']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)

        if write_header:
            writer.writeheader()

        writer.writerow({'id': giveaway.id,
                         'timestamp': str(timestamp)
                         }
                        )
