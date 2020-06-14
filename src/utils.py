import itertools
import re
import threading
import time

anim_thread = None
anim_stopped = False


def extract_id_from_url(url):
    if url.count("gleam.io") > 0:
        id_match = re.search(r"\w+/(\w{5})[/-]", url)
    elif url.count("playr.gg") > 0:
        id_match = re.search(r"/([\w-]{7})$", url)
    else:
        return None

    if not id_match:
        return None

    return id_match.group(1)


def filter_giveaways(giveaways, history_ids, error_ids):
    new_list = []
    seen_ids = set()

    for giveaway in giveaways:
        if giveaway.id not in history_ids and giveaway.id not in error_ids and giveaway.id not in seen_ids:
            new_list.append(giveaway)
            seen_ids.add(giveaway.id)

    return new_list


def loading_text_anim(display_text):
    for c in itertools.cycle(['|', '/', '-', '\\']):
        if anim_stopped:
            break

        string = f" {c}  {display_text}"
        print('\r' + string, end='')
        time.sleep(1)


def start_loading_text(progress_text):
    global anim_stopped, anim_thread

    anim_stopped = False

    anim_thread = threading.Thread(target=loading_text_anim, args=[progress_text])
    anim_thread.start()


def stop_loading_text(finish_text=None):
    global anim_stopped

    anim_stopped = True
    if anim_thread:
        anim_thread.join()

        if finish_text:
            print(f'\r{finish_text}                                                      \n', end='')
