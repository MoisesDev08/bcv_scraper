from pathlib import Path
from random import uniform
from time import sleep

import bcv.scraper.validation as v
from bcv.config.config import URL_BASE, URL_WITH_XLS_FILES
from bcv.scraper.downloader import Downloader
from bcv.scraper.exceptions import HTMLInvalidWarning
from bcv.scraper.html_parser import DolarRateScraper, HTMLScraper, LinksXLSFilesScraper
from bcv.scraper.http_client import HttpClient


def _get_dolar_html(client: HttpClient):

    response_dolar_html = client.fetch(URL_BASE)
    valid_html_dolar = v.validate_html(response_dolar_html)

    if valid_html_dolar is not True:
        raise HTMLInvalidWarning(valid_html_dolar=valid_html_dolar)

    html_dolar = response_dolar_html.text
    return html_dolar


def _get_recent_links_html(client: HttpClient):

    response_links_html = client.fetch(URL_WITH_XLS_FILES)
    valid_html_links = v.validate_html(response_links_html)

    if valid_html_links is not True:
        raise HTMLInvalidWarning(valid_html_links=valid_html_links)

    html_links = response_links_html.text
    return html_links


def _get_html_scraper(
    client: HttpClient | None = None, links_flag: bool = True, dolar_flag: bool = True
) -> HTMLScraper | DolarRateScraper | LinksXLSFilesScraper:

    if not client:
        client = HttpClient()

    if links_flag and dolar_flag:
        links_html = _get_recent_links_html(client)
        sleep(uniform(1.24, 2.36))

        dolar_html = _get_dolar_html(client)
        scraper = HTMLScraper(html_dolar=dolar_html, html_links=links_html)

    elif not links_flag and dolar_flag:
        dolar_html = _get_dolar_html(client)
        scraper = DolarRateScraper(dolar_html)

    elif links_flag and not dolar_flag:
        links_html = _get_recent_links_html(client)
        scraper = LinksXLSFilesScraper(links_html)

    return scraper


def get_today_dolar_rate(
    scraper: HTMLScraper | DolarRateScraper | None = None,
    client: HttpClient | None = None,
):

    if not scraper:
        scraper = _get_html_scraper(client, links_flag=False, dolar_flag=True)

    if isinstance(scraper, HTMLScraper):
        data_tuple = scraper.get_dolar_rate()

    elif isinstance(scraper, DolarRateScraper):
        data_tuple = scraper.fetch_data()

    date = data_tuple[0]
    rate = data_tuple[1]

    return {"date": date.strftime("%d %B, %Y"), "rate": rate, "datetime": date}


def get_recent_history_files_links(
    client: HttpClient | None = None, scraper: HTMLScraper | LinksXLSFilesScraper = None
):

    if not scraper:
        scraper = _get_html_scraper(client=client, dolar_flag=False, links_flag=True)

    if isinstance(scraper, HTMLScraper):
        list_link_tuples = scraper.get_links()

    elif isinstance(scraper, LinksXLSFilesScraper):
        list_link_tuples = scraper.get_links()

    return list_link_tuples


def download_all_rate_history_files(
    path: Path, client: HttpClient | None = None, mkdir: bool = False, pages: int = 3
):

    downloader = Downloader(downloads_dir=path, mkdir=mkdir, client=client)
    downloader.download(pages)


def run_pipeline():
    client = HttpClient()
    for page in range(0, 5):
        response = client.fetch(page=page)
        html = response.text
        scraper = HTMLScraper(html_dolar=html, html_links=html)

        data = scraper.get_dolar_rate()
        date = str(data[0])
        rate = data[1]
        links = scraper.get_links()
        print(
            (
                f"{'=' * 40}\n{f'PAGE N°{page}':^40}\n{'=' * 40}\n"
                f"{'TASA: ':<}\t{rate}\n"
                f"{'FECHA VALOR: ':<}\t{date}\n"
                f"{'LINKS: ':<}\n"
            )
        )
        for link in links:
            print(link)

        if not scraper.links_scraper._next_page_enabled():
            print("Program Finished")
            break


if __name__ == "__main__":
    import csv

    from bcv.config.config import DATA_DIR, XLS_HISTORY_DIR
    from bcv.scraper.xls_parser import XLSParser

    download_all_rate_history_files(XLS_HISTORY_DIR, HttpClient(), mkdir=True)
    parser = XLSParser(XLS_HISTORY_DIR)
    rates_generator = parser.run()

    f_path = DATA_DIR / "rates.csv"
    for date, rate in rates_generator:
        with f_path.open(mode="a+", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f=f, fieldnames=("date", "rate"))
            data_dict = {"date": date.strftime("%Y/%m/%d"), "rate": rate}

            writer.writerow(data_dict)
