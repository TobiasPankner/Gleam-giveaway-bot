from requests import get
from requests_toolbelt.threaded import pool


def get_urls_gleamlist():
    url = 'http://gleamlist.com:5000/api?page={}&order=undefined&locations'
    gleam_urls = []

    # get the total amount of pages on the site

    urls_to_scrape = [url.format(page_num) for page_num in range(1, 20)]

    # Get all responses with multithreading
    p = pool.Pool.from_urls(urls_to_scrape)
    p.join_all()

    for response in p.responses():
        if response.status_code != 200:
            continue

        data = response.json()
        urls = [result["url"] for result in data["data"]["results"]]

        if len(urls) == 0:
            continue

        gleam_urls.extend(urls)

    return gleam_urls


def get_urls_playrgg():
    # graphql query taken directly from the playr.gg site
    url = 'https://api.playr.gg/graphql?operationName=contestsBrowse&variables={"limit":500,"age":18,"country":null,"sort":"expiration:asc","keywords":null,"entered":null,"method":null,"designation":null}&extensions={"persistedQuery":{"version":1,"sha256Hash":"1977eb0b082dbbb9a0b06d27f59bda93ee60ad1c197d406a741a80181df34445"}}'

    response = get(url)
    if response.status_code != 200:
        return []

    result = response.json()

    urls = [f"https://playr.gg/giveaway/{contest['idToken']}" for contest in result['data']['contests']]

    return urls
