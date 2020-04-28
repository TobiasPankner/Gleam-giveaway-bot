from requests import get
from bs4 import BeautifulSoup


def get_urls_gleamlist():
    url = 'http://gleamlist.com'
    gleam_urls = []

    print(f"Pulling links from {url}")

    for page_num in range(1, 30):
        response = get(f"{url}/index.php?page={page_num}")

        html_soup = BeautifulSoup(response.text, 'html.parser')

        url_elems = html_soup.select("tbody>tr>td>div>a[href*='gleam.io']")

        if len(url_elems) == 0:
            break

        for url_elem in url_elems:
            gleam_urls.append(url_elem['href'])

        print(f"Found {len(url_elems)} links on page number {page_num}")

    print(f"Pulled {len(gleam_urls)} links from {url}\n")
    return gleam_urls