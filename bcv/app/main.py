from bcv import config as cf
from bcv.scraper.http_client import HttpClient
from bcv.scraper.html_parser import DolarRateScraper
from bcv.scraper.exceptions import *
import logging

logger = logging.getLogger(__name__)

def main():
    try:    
        cf.setup_logging_config()
        client = HttpClient()
        for _ in range(6):
            r = client.fetch(_)
            dolar_scraper = DolarRateScraper(r)
            dolar_info = dolar_scraper.get_data
            
    except MiBaseException as e:

        logger.error(
            "Error esperado:\n%s",
            "DATA & CONTEXT\n%s",
            f"{e.__repr__()}",
              exc_info=True
              )
        raise

    except Exception as e:
        logger.fatal(f"Error inesperado:\n{e}", exc_info=True)
        raise
        
main()