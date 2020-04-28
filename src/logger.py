import os

history_dir = "../data/"
history_file_name = "history.csv"
header = "\"url\",\"name\",\"id\",\"my_entries\",\"avaliable_entries\",\"total_entries\",\"win_chance\",\"ends_at\""


def write_log(giveaway_info, user_info):
    campaign = giveaway_info['campaign']
    contestant = user_info['contestant']

    my_entries = sum([entry[0]['w'] for entry in contestant['entered'].values()])
    avaliable_entries = sum([int(method['worth']) for method in giveaway_info['entry_methods']])
    win_chance = my_entries / giveaway_info['total_entries'] if giveaway_info['total_entries'] > 0 else -1

    data = f"\"{campaign['stand_alone_url']}\",\"{campaign['name']}\",\"{campaign['key']}\",\"{my_entries}\",\"{avaliable_entries}\",\"{giveaway_info['total_entries']}\",\"{round(win_chance * 100, 2)}%\",\"{campaign['ends_at']}\""
    # ignore emojis and other unicode
    data = data.encode('ascii', 'ignore')

    if not os.path.isdir(history_dir):
        os.mkdir(history_dir)

    if not os.path.isfile(f"{history_dir}{history_file_name}"):
        with open(f"{history_dir}{history_file_name}", 'w') as file:
            file.write(header)

    with open(f"{history_dir}{history_file_name}", 'a') as file:
        file.write("\n")
        file.write(data.decode())

