import csv
import os


def write_log(filename, giveaway_info, user_info):
    campaign = giveaway_info['campaign']
    contestant = user_info['contestant']

    my_entries = sum([entry[0]['w'] for entry in contestant['entered'].values()])
    available_entries = sum([int(method['worth']) for method in giveaway_info['entry_methods']])

    total_entries = giveaway_info['total_entries']
    total_entries_str = str(total_entries) if total_entries > 0 else ""
    win_chance_str = str(round((my_entries / total_entries) * 100, 4)) + '%' if giveaway_info[
                                                                                    'total_entries'] > 0 else ""

    write_header = False if os.path.isfile(filename) else True

    with open(filename, 'a', newline='') as csvfile:
        fieldnames = ['url', 'name', 'id', 'my_entries', 'available_entries', 'total_entries', 'win_chance', 'ends_at']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)

        if write_header:
            writer.writeheader()

        writer.writerow({'url': campaign['stand_alone_url'],
                         'name': campaign['name'].encode('ascii', 'ignore').decode(),
                         'id': campaign['key'],
                         'my_entries': str(my_entries),
                         'available_entries': str(available_entries),
                         'total_entries': total_entries_str,
                         'win_chance': win_chance_str,
                         'ends_at': str(campaign['ends_at'])
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
