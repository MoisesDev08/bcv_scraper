import logging
from pathlib import Path
from typing import Iterable

from requests import Response

from bcv.scraper import validation as v
from bcv.scraper.exceptions import (
    DownloadError,
    EmptyFileError,
    HTMLInvalidWarning,
    NotAExcelFile,
)
from bcv.scraper.html_parser import LinksXLSFilesScraper
from bcv.scraper.http_client import HttpClient

logger = logging.getLogger(__name__)


class Downloader:
    def __init__(
        self,
        downloads_dir: str | Path,
        mkdir: bool = False,
        client: HttpClient | None = None,
    ):
        self.client = HttpClient() if not client else client
        self.downloads_dir = v.validate_downloads_dir(downloads_dir, mkdir=mkdir)
        self._downloads_hashes = self._calculate_hashes_in_directory(self.downloads_dir)

    def _calculate_hashes_in_directory(self, path: Path):

        hashes = set()
        dir_iter = path.iterdir()
        for path in dir_iter:
            if path.is_file():
                hash_file = v.calculate_hash_file(path)
                hashes.add(hash_file)

        return hashes

    def _is_already_in_the_hashes(self, objeto: Path | Response):

        if isinstance(objeto, Response):
            h = v.calculate_hash_response(objeto)

        elif isinstance(objeto, Path):
            h = v.calculate_hash_file(objeto)

        else:
            raise RuntimeError(
                f"TypeError: Path | Response object expected, given: {type(objeto)}"
            )

        flag = h in self._downloads_hashes
        return flag

    def _links_scraper_generator(self, pages: int):

        for page_number in range(0, pages):
            try:
                if page_number == 0:
                    page_number = None
                response = self.client.fetch(page=page_number)
                v.validate_html(response)

                html = response.text
                scraper = LinksXLSFilesScraper(html=html)

            except HTMLInvalidWarning:
                logger.warning(
                    f"Error parsing page N°{page_number if page_number else 'N/A'}"
                )
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug("Traceback", exc_info=True)

                continue

            yield scraper

            if not scraper.next_page:
                logger.info(
                    "Stopping scraper generator because of could not found 'Next Page' button"
                )
                break

    def _choose_ext_helper(self, get_ext, headers_ext):
        if get_ext and headers_ext:
            if not get_ext == headers_ext:
                logger.warning(
                    "Diferentes extensiones detectadas, usando la de la peticion GET..."
                )
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f"get_ext=({get_ext}), head_ext=({headers_ext})")

                ext = get_ext

            elif get_ext == headers_ext:
                ext = get_ext

        elif get_ext and not headers_ext:
            ext = get_ext

        elif not get_ext and headers_ext:
            ext = headers_ext

        else:
            ext = None

        return ext

    def _to_download_xls_and_save(
        self, link: str, name: str, destination: Path, ext=None
    ):

        link = v.validate_url(link)
        r_get = self.client.fetch(link)
        if self._is_already_in_the_hashes(r_get):
            raise RuntimeError("Hash duplicado detectado.\nContinuando...")

        try:
            r_head = self.client.fetch(url=link, head=True)
        except Exception:
            r_head = None

        if ext is None:
            get_ext, headers_ext = v.validate_excel_extension(
                r_get=r_get, r_head=r_head
            )
            ext = self._choose_ext_helper(get_ext=get_ext, headers_ext=headers_ext)

        if ext is None:
            raise NotAExcelFile(
                "No es un archivo excel", link=link, name=name, destination=destination
            )

        if ext and isinstance(ext, str):
            name = name + ext
        path = destination / f"{name}"
        path.write_bytes(r_get.content)

        del r_get
        del r_head

    def download(self, pages_quantity: int):
        """
        ### Args:

        -   pages_quantity (int): number of pages wich would to scrape the excel
        history rate files from the '*Banco Central de Venezuela*' oficial page

        ### Note:

        -   The pages_quantity param is used as last page indicator in a
        range(0, pages_quantity) while it is detected the button 'Next Page'
        in the page, if any button is detected raise a Warning and continue
        scraping with the valid pages detected so far.
        """

        with self.client.session:
            scraper_generator: Iterable[LinksXLSFilesScraper] = (
                self._links_scraper_generator(pages_quantity)
            )
            for scraper in scraper_generator:
                links_list: list[tuple[str, str]] = scraper.get_links()
                for link_tuple in links_list:
                    name, link = link_tuple
                    destination = self.downloads_dir

                    try:
                        self._to_download_xls_and_save(
                            link=link, name=name, destination=destination
                        )
                    except NotAExcelFile:
                        logger.critical(
                            "No extension detected, downloading without a extension..."
                        )
                        ext = ""
                        name = name + ext

                        self._to_download_xls_and_save(
                            link=link, name=name, destination=destination
                        )

                        if logger.isEnabledFor(logging.DEBUG):
                            logger.debug(f"ulr={link}\npath={destination}\nname={name}")
                        continue

                    except EmptyFileError:
                        logger.warning(f"Empty file: {name}")
                        if logger.isEnabledFor(logging.DEBUG):
                            logger.debug((f"url={link}"))
                        continue

                    except DownloadError as d:
                        logger.error(f"DownloadError: {d}")
                        logger.info("Continue...")
                        continue

                    except RuntimeError as r:
                        logger.warning(f"{str(r)}")
                        print(r)
                        continue
