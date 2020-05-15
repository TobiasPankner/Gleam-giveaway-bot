from requests import get
from bs4 import BeautifulSoup
from requests_toolbelt.threaded import pool


def get_urls_gleamlist():
    url = 'http://gleamlist.com'
    gleam_urls = []

    # get the total amount of pages on the site
    response = get(url)
    html_soup = BeautifulSoup(response.text, 'html.parser')
    url_elem = html_soup.select("tbody>script")

    if len(url_elem) > 0:
        total_pages = int(str(url_elem[0].contents[0]).replace("var last = ", ""))
    else:
        total_pages = 30

    urls_to_scrape = [f"{url}/index.php?page={page_num}" for page_num in range(1, total_pages+1)]

    # Get all responses with multithreading
    p = pool.Pool.from_urls(urls_to_scrape)
    p.join_all()

    for response in p.responses():
        html_soup = BeautifulSoup(response.text, 'html.parser')

        url_elems = html_soup.select("tbody>tr>td>div>a[href*='gleam.io']")

        if len(url_elems) == 0:
            break

        for url_elem in url_elems:
            gleam_urls.append(url_elem['href'])

    return gleam_urls
