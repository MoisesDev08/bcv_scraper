import requests
from tenacity import (
    retry, retry_if_exception_type, 
    stop_after_delay, wait_exponential_jitter,
    after_log
)

import fake_useragent
from bcv import config as cf
import logging
import requests.exceptions

logger = logging.getLogger(__name__)

class RetryableError(Exception): pass
class HttpClient():

    def __init__(self):
        self.session = requests.Session()
        try:
            self.ua = fake_useragent.UserAgent()
        except Exception:
            logger.debug("fake_useragent failed, using fallback UA")
            self.ua = None

    @staticmethod
    def _fallback_user_agent_helper():
    
        logger.debug("Calling to _fallback_user_agent_helper()")
        ua = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/148.0.0.0 Safari/537.36 Edg/148.0.0.0"
        )
        
        return ua

    def _get_user_agent(self):
        try:

            logger.debug("Calling to _get_user_agent()")
            if self.ua:
                ua = self.ua.random
                logger.debug(f"User-Agent gotten:\n{ua}")
                return ua

            ua = self._fallback_user_agent_helper()
            logger.debug(f"User-Agent gotten:\n{ua}")
            return ua
        
        except Exception:

            logger.debug("Error during call to _get_user_agent()", exc_info=True)
            return self._fallback_user_agent_helper()

            
    def _get_headers(self): 

        try:
            logger.debug("Calling to _get_headers()")
            headers = {
                "accept": (
                    "text/html,application/xhtml+xml,"
                    "application/xml;q=0.9,image/avif,"
                    "image/webp,image/apng,*/*;q=0.8,"
                    "application/signed-exchange;v=b3;q=0.7"
                ),
                "accept-language": "en-US,en;q=0.9,es-MX;q=0.8,es;q=0.7",
                "referer": "https://www.bcv.org.ve/",
                "user-agent": self._get_user_agent()  
            }

            logger.debug(f"Headers gotten:\n{headers}")
            return headers
        except Exception:
            logger.error("Error during call to _get_headers()", exc_info=True)
            raise


    @retry(
            retry=retry_if_exception_type((
                requests.exceptions.ConnectionError, 
                requests.exceptions.Timeout,
                RetryableError)),
            stop=stop_after_delay(30),
            wait=wait_exponential_jitter(exp_base=2, max=10),
            after=after_log(logger, logging.WARNING)
    )
    def fetch(self, page: int = None):

        response = None
        try:

            logger.debug("Calling to fetch()")
            response = self.session.get(
                    url=cf.URL_WITH_XLS_FILES,
                    headers=self._get_headers(),
                    verify=cf.CERT_PATH,
                    params={"page": page}
                )
            
            if response is None:
                logger.debug(f"Response object was never created")
                raise RetryableError

            response.raise_for_status()
            logger.debug("Fetching Succesfully!")
            return response.text
        
        except Exception as e:
            
            logger.info(f"Error during call to fetch():\n{e}")
            status = getattr(response, 'status_code', None)
            if status in (429, 500): raise RetryableError
            else: 
                logger.error("Error during call to fetch()", exc_info=True)
                raise e

if __name__ == '__main__':
    
    cf.setup_logging_config()
    client = HttpClient()
    print(client.fetch()[:2000])