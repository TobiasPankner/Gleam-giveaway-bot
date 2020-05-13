import itertools
import re
import threading
import time

anim_thread = None
anim_stopped = False


def filter_urls(urls_to_filter, history_ids):
    # remove unnecessary info of the url and ignore previously visited
    for i, url in enumerate(urls_to_filter):
        id_re = re.search(r"\w+/(\w{5})[/-]", url)
        if not id_re:
            urls_to_filter[i] = ""
            continue

        id_str = id_re.group(1)

        new_url = f"https://gleam.io/{id_str}/a"
        if id_str not in history_ids:
            urls_to_filter[i] = new_url
        else:
            urls_to_filter[i] = ""

    urls = [url for url in urls_to_filter if url != ""]
    urls = list(dict.fromkeys(urls))

    return urls


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


def stop_loading_text(finish_text=None, newline=False):
    global anim_stopped

    anim_stopped = True
    anim_thread.join()

    if finish_text:
        print(f'\r{finish_text}                                                      \n', end='')
    if newline:
        print("")
