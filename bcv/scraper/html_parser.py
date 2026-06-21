from bcv import config as cf
from bcv.scraper.exceptions import HTMLParserError, SelectorNotFound
from bs4 import BeautifulSoup, Tag
from datetime import datetime
from typing import Any
from dateutil.parser import parse
import logging, re

logger = logging.getLogger(__name__)

class DolarRateScraper: 
    """Class with all the logic related to the dolar rate scraping
    
    ### Params

    * *html (str):* the HTML from the 'Banco Central de Venezuela' oficial page 
    or 'Tipo de Cambio de Referencia (SMC)' page loaded as one string
    
    #### Notes:
    
    - The class doesn't have logic beyond the HTML scraping"""

    def __init__(self, html: str) -> None:
        self.soup_dolar = BeautifulSoup(html, "lxml")
        self._dolar = None
        self._fecha_valor = None

    def _validate_dolar_rate(self, value: str | float | int) -> float:

        if isinstance(value, str):
                v = value.replace(",", ".").strip()
                try:
                    return float(v)
                except ValueError:
                    raise HTMLParserError(f"Tasa no convertible: value=({value})")
            
        elif isinstance(value, (int, float)):

            if value < 0: raise HTMLParserError(f"Tasa no puede ser negativa: value=({value})")
            return float(value)
        
        else: 
            raise HTMLParserError(
                "TypeError during rate validation",
                value=value, type_value=type(value)
                )
            
    @property
    def dolar(self) -> float | None:
        return self._dolar
    
    @dolar.setter
    def dolar(self, value: str | float | int):
        v = self._validate_dolar_rate(value)
        self._dolar = v

    def _get_dolar_rate(self) -> float:

        dolar_tag = self.soup_dolar.select_one(cf.DOLAR_RATE_SELECTOR)
        if dolar_tag is None:

            html_id_dolar = self.soup_dolar.select_one("div#dolar")
            if isinstance(html_id_dolar, Tag): 
                html_id_dolar = html_id_dolar.prettify()[:400]

            raise SelectorNotFound(
                "Could not find dolar_tag in HTML",
                selector=cf.DOLAR_RATE_SELECTOR,
                html_chunck=html_id_dolar,
                html_chunck_selector="div#dolar"
                )

        rate = dolar_tag.get_text(strip=True)
        if logger.isEnabledFor(logging.DEBUG):

            logger.debug(f"dolar tag gotten, pretty=({dolar_tag.prettify()[:200]})")
            logger.debug(f"dolar tag gotten, text=({rate})")

        self.dolar = rate
        logger.info(f"Dolar rate gotten from page; {rate}")
        
        return self.dolar

    def _get_dolar_date(self) -> datetime:

        date_tag = self.soup_dolar.select_one(cf.FECHA_VALOR_DOLAR_SELECTOR)
        if date_tag is None: 
            raise SelectorNotFound(
                "Could not find date_tag in HTML",
                selector=cf.FECHA_VALOR_DOLAR_SELECTOR
            )

        if logger.isEnabledFor(logging.DEBUG):

            logger.debug(f"date tag gotten, pretty=({date_tag.prettify()[:200]})")
            logger.debug(f"date tag gotten, text=({date_tag.get_text(strip=True)})")
        
        self.fecha_valor = date_tag
        return self.fecha_valor

    def _validate_date_helper(self, value: Tag) -> datetime:

        fecha = value.get("content") # Tag["content"] tiene fecha en formato ISO 8601
        if fecha is None:
                raise HTMLParserError(
                    "Tag has no 'content' attribute",
                    value=value,
                    pretty=value.prettify()[:400]
                    )

        if isinstance(fecha, list): raise HTMLParserError(
            "Unexpected HTML attribute value. "
            "Expected: str[ISO 8601 FORMAT date]", 
            value_content_attr=fecha
            )
        
        if not re.fullmatch(cf.ISOFORMAT_PATTERN, fecha): raise HTMLParserError(
            "Date has not ISO 8601 FORMAT",
            fecha=fecha,
            fmt_expected=cf.ISOFORMAT_PATTERN
            )
        
        try: return datetime.fromisoformat(fecha)
        except ValueError: 

            try: return parse(fecha)
            except ValueError as e:

                raise HTMLParserError(
                    "ValueError raised for datetime during date validation",
                    fecha=fecha
                ) from e

    def _validate_date(self, value: Tag) -> datetime:

        if  isinstance(value, Tag):
            return self._validate_date_helper(value)

        else:
            raise HTMLParserError(
                "TypeError during date validation, "
                f"Tag object expected, ({type(value).__name__}) gotten",
                value=value
                )
            
    @property
    def fecha_valor(self) -> datetime | None:
        return self._fecha_valor
    
    @fecha_valor.setter
    def fecha_valor(self, value: Tag):
        self._fecha_valor = self._validate_date(value)

    def fetch_data(self) -> tuple[datetime, float]:
        """Scrape the dolar data from the HTML on self.html
        
        ### Return: 
        *(tuple[date, dolar_rate])*

        * *date (datetime):* datetime obj with the date from the dolar rate
        * *dolar_rate (float):* dolar rate in float obj"""

        if self.fecha_valor is None: self._get_dolar_date()
        if self.dolar is None: self._get_dolar_rate()

        return (
            self.fecha_valor,
            self.dolar
        )

class LinksXLSFilesScraper: 
    """Class with all the logic related to the dolar rate history scraping
    within .xls files. Shows the links to those files like a list[str] in self.links 
    
    ### Params

    * *html (str):* the HTML from the 'Tipo de Cambio de Referencia (SMC)' page
    loaded as one string
    
    #### Notes:
    
    - This class doesn't have logic beyond the HTML scraping"""
    def __init__(self, html: str):
        self.soup_links = BeautifulSoup(html, 'lxml')
        self._links = None

    def _links_validator_helper(self, list_links_tags: dict[str, Tag]) -> list[tuple[str, str]]: 
        
        hf_err = 0
        valid_links = []
        for k, tag in list_links_tags.items():

            href = tag.get("href").strip()
            if isinstance(href, str) and href.endswith(".xls"):
                valid_links.append((k, href))
            
            else:
                hf_err += 1
                logger.warning(f"Tag N°{hf_err} with either invalid or none link")

                if logger.isEnabledFor(logging.DEBUG) and href: 
                    logger.debug(f"Tag without link to .xls or bad formatted link:\n{href}")
                
                continue

        if logger.isEnabledFor(logging.DEBUG): logger.debug(f"{hf_err} errors during links validation")
        return valid_links
        
    def _get_links_helper(self, tr_tags: list[Tag]) -> dict:

            title_selector = "td.views-field.views-field-title"
            list_links_tags = {}
            for tag in tr_tags:

                title_tag = tag.select_one(title_selector)
                link_tag = tag.select_one(cf.LINK_SELECTOR)

                if title_tag is None: 
                    logger.warning("Could not find title Tag element in row, continue...")
                    if logger.isEnabledFor(logging.DEBUG):
                        logger.debug(f"Row tag without title element; {tag.prettify()[:150]}")
                    
                    continue

                if link_tag is None:
                    logger.warning("Could not find link Tag element in row, continue...")
                    if logger.isEnabledFor(logging.DEBUG):
                        logger.debug(f"Row tag without link element; {tag.prettify()[:150]}")
                    
                    continue
                
                k = title_tag.get_text(strip=True)
                list_links_tags[k] = link_tag

            return list_links_tags
        
    def get_links(self) -> list[tuple[str, str]]:
        """Make the HTML scraping and give a list with the links of the XLS files
        
        - **Return**: ***list[tuple[name, url]]***
            -   name (str): File name from the scraping
            -   url (str): Link for do the get request and download the file
            """

        table_tag = self.soup_links.select_one(cf.TABLE_SELECTOR)
        if table_tag is None: 

            raise SelectorNotFound(
                "Could not find table Tag element",
                selector=cf.TABLE_SELECTOR
            )
        
        tr_tags = table_tag.select("tbody > tr")
        if not tr_tags:

            raise SelectorNotFound(
                "Could not find rows 'tr' Tag elements in table",
                selector=(cf.TABLE_SELECTOR + "tbody > tr"),
                table_chunk=table_tag.prettify()[:300]
            )
        
        dict_links_tags = self._get_links_helper(tr_tags)
        self.links = dict_links_tags
        return self.links
    
    def next_page_enabled(self) -> bool:

        selector = cf.NEXT_PAGE_SELECTOR
        tag = self.soup_links.select(selector)
        len_tag = len(tag)
        if len_tag > 1: raise HTMLParserError(
            "Multiple 'Next Page' buttons were found.", 
            len_tag=len_tag, 
            tag=[x.prettify()[:100] for x in tag],
            selector=selector
            )
        
        if len_tag == 0: 
            logging.warning("No 'Next Page' button were found. This might be the last page")
            return False

        return True
    
    @property
    def links(self):
        return self._links
    
    @links.setter
    def links(self, value: list[dict[str, Tag]]):
        v = self._links_validator_helper(value)
        self._links = v


class HTMLScraper:
    """HTMl scraper with utils for scrape the dolar rate or the links to
    the files with the dolar rate history.

    *Use los métodos **self.get_links** y **self.get_dolar_rate** para obtener datos y evitar
    problemas de acceso en la composición*

    *Si insiste en los scrapers use cada scraper individualmente segun la accion para evitar problemas 
    de acceso, los scrapers estan expuestos en **self.dolar_scraper** y **self.links_scraper*** 
    
    ### Params

    * *html_dolar (str):* the HTML from the 'Banco Central de Venezuela' oficial page 
    or 'Tipo de Cambio de Referencia (SMC)' page loaded as one string

    * *html_links (str):* the HTML from the 'Tipo de Cambio de Referencia (SMC)' page
    loaded as one string
    
    #### Notes:
    
    - This class doesn't have logic beyond the HTML scraping
    - The attr self.dolar_scraper has a DolarRateScraper(html_dolar) obj
    - The attr self.links_scraper has a LinksXLSFilesScraper(html_links) obj"""
    
    def __init__(self, html_dolar: str, html_links: str):
        self.dolar_scraper = DolarRateScraper(html_dolar)
        self.links_scraper = LinksXLSFilesScraper(html_links)

    def get_links(self):
        return self.links_scraper.get_links()
    
    def get_dolar_rate(self):
        return self.dolar_scraper.fetch_data()