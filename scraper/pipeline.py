from bcv.scraper.exceptions import *
from bcv.scraper.http_client import HttpClient
from bcv.scraper.html_parser import HTMLScraper, DolarRateScraper, LinksXLSFilesScraper
from bcv.scraper.downloader import Downloader
from bcv.config import setup_logging_config, URL_WITH_XLS_FILES, URL_BASE
from bcv.scraper.validation import * 
from random import uniform
from time import sleep
from bcv import config as cf


def _get_dolar_html(client: HttpClient):

    response_dolar_html = client.fetch(URL_BASE)
    valid_html_dolar = validate_html(response_dolar_html)

    if not valid_html_dolar is True:
        raise HTMLInvalidWarning(valid_html_dolar=valid_html_dolar)
    
    html_dolar = response_dolar_html.text
    return html_dolar

def _get_recent_links_html(client: HttpClient):

    response_links_html = client.fetch(URL_WITH_XLS_FILES)
    valid_html_links = validate_html(response_links_html)

    if not valid_html_links is True:
        raise HTMLInvalidWarning(valid_html_links=valid_html_links)
    
    html_links = response_links_html.text
    return html_links

def _get_html_scraper(
        client: HttpClient | None = None, 
        links_flag: bool = True,
        dolar_flag: bool = True
    ) -> HTMLScraper | DolarRateScraper | LinksXLSFilesScraper:

    if not client: client = HttpClient()

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
        scraper = _get_html_scraper(
            client, 
            links_flag=False,
            dolar_flag=True
            )

    if isinstance(scraper, HTMLScraper):
        data_tuple = scraper.get_dolar_rate()

    elif isinstance(scraper, DolarRateScraper):
        data_tuple = scraper.fetch_data()

    date = data_tuple[0]
    rate = data_tuple[1]

    return {
        "date": date.strftime("%d %B, %Y"),
        "rate": rate,
        "datetime": date
    }

def get_recent_history_files_links(
        client: HttpClient | None = None,
        scraper: HTMLScraper | LinksXLSFilesScraper = None
        ):
    
    if not scraper:
        scraper = _get_html_scraper(
            client=client,
            dolar_flag=False,
            links_flag=True
            )
        
    if isinstance(scraper, HTMLScraper):
        list_link_tuples = scraper.get_links()

    elif isinstance(scraper, LinksXLSFilesScraper):
        list_link_tuples = scraper.get_links()
    
    return list_link_tuples

def download_all_rate_history_files(path: Path, client: HttpClient | None = None, mkdir: bool = False):

    cf.setup_logging_config()
    downloader = Downloader(downloads_dir=path, mkdir=mkdir, client=client)
    downloader.download(5)
download_all_rate_history_files(path=Path(__file__).parent.parent.parent / 'data_temp', mkdir=True)

def run_pipeline():
    setup_logging_config()
    client = HttpClient()
    for page in range(0, 5):

        response = client.fetch(page=page)
        html = response.text
        scraper = HTMLScraper(html_dolar=html, html_links=html)
        
        data = scraper.get_dolar_rate()
        date = str(data[0])
        rate = data[1]
        links = scraper.get_links()
        print((
            f"{'=' * 40}\n{f'PAGE N°{page}':^40}\n{'=' * 40}\n"
            f"{f'TASA: ':<}\t{rate}\n"
            f"{f'FECHA VALOR: ':<}\t{date}\n"
            f"{f'LINKS: ':<}\n"
        ))
        for link in links: print(link)

        if not scraper.links_scraper.next_page_enabled(): 
            print("Program Finished")
            break