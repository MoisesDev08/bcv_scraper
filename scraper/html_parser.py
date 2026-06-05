from bcv import config as cf
from bs4 import BeautifulSoup, StopParsing
import logging

logger = logging.getLogger(__name__)

class DolarRateScraper: 
    def __init__(self, html: BeautifulSoup):
        self.html = html
        self._dolar = None

    def _validator_helper(self, value):

        if isinstance(value, str):
                v = value.replace(",", ".").strip()
                assert v.replace(".", "", 1).isnumeric()
                return float(v)
            
        elif isinstance(value, (int, float)):
            return float(value)
        
        else: 
            logger.debug(
                "TypeError during call to _validate_dolar_rate(), expected; str | int | float"
                f"type_value_gotten=({type(value)})\n"
                f"value_gotten=({value})"
            )
            raise TypeError("TypeError during call to _validate_dolar_rate(), expected; str | int | float")
        
    def _validate_dolar_rate(self, value: str | int | float):

        try:

            return self._validator_helper(value)
        
        except AssertionError:

            logger.error("Unexpected value gotten during rate validation")
            logger.debug(
                f"type_value_gotten=({type(value)})\n"
                f"value_gotten=({value})"
                )
            raise
            
        except Exception:
            logger.error("Error during call to _validate_dolar_rate()", exc_info=True)
            raise

    @property
    def dolar(self):
        return self._dolar
    
    @dolar.setter
    def dolar(self, value):
        v = self._validate_dolar_rate(value)
        self._dolar = v

    def dolar_rate(self):

        try:
            logger.debug("Calling to dolar_rate()")
            html_tag = self.html
            dolar_tag = html_tag.select_one(cf.DOLAR_RATE_SELECTOR)
            
            if dolar_tag is None:
                logger.debug(
                        "Error trying to capture dolar_tag"
                        f"selector used=({cf.DOLAR_RATE_SELECTOR})"
                    )
                raise ValueError("Could not find dolar_tag in HTML")

            
            logger.debug(f"dolar_tag gotten, text=({dolar_tag.get_text(strip=True)})")
            rate = dolar_tag.get_text(strip=True)
            
            self.dolar = rate
            return self.dolar
        
        except Exception:
            logger.error("Error during call to dolar_rate()", exc_info=True)
            raise


class LinksXLSFilesScraper: pass